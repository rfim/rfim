"""Synthetic non-CDC file ingestion: safe repair, row quarantine, and replay.

This local SQLite model uses the Beacon route in the shared YAML. It does not
connect to S3, Delta Lake, or a live AI service.

Run: pip install -r examples/requirements.txt
     python examples/non_cdc_self_heal_demo.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable

import yaml

CONFIG = Path(__file__).with_name("multitenant-ingestion.yaml")
DECIMAL_2 = re.compile(r"^[+-]?\d+(?:\.\d{1,2})?$")


@dataclass(frozen=True)
class ObjectBatch:
    tenant: str
    dataset: str
    bucket: str
    key: str
    version_id: str
    body: bytes

    @property
    def checksum(self) -> str:
        return hashlib.sha256(self.body).hexdigest()

    @property
    def identity(self) -> tuple[str, str, str, str, str]:
        return self.tenant, self.dataset, self.bucket, self.key, self.version_id


def load_route(tenant: str, dataset: str) -> dict[str, Any]:
    config = yaml.safe_load(CONFIG.read_text())
    for item in config["tenants"]:
        if item["id"] == tenant:
            for route in item["datasets"]:
                if route["name"] == dataset:
                    return {**route, "tenant_id": tenant}
    raise ValueError(f"Unknown route: {tenant}/{dataset}")


def field_type(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    return type(value).__name__


class FileGuardrails:
    def __init__(self, route: dict[str, Any]):
        if route["source"]["type"] != "s3_files":
            raise ValueError("This reference supports only the Beacon file route")
        policy = route["non_cdc"]
        if policy["ai_advisory"] != {"input": "schema_metadata_only", "auto_approve": False}:
            raise ValueError("AI must receive metadata only and cannot approve repairs")
        if (policy["on_unknown_field"] != "hold_file_for_review" or
                policy["on_unrepairable_row"] != "quarantine_row"):
            raise ValueError("Unknown schemas must hold; unrepairable rows must quarantine")
        rules = policy["self_heal"]["approved_rules"]
        if rules != [{"field": "amount", "when": "numeric_string_with_at_most_2_decimals",
                      "action": "exact_decimal_cast"}]:
            raise ValueError("Only the declared exact decimal cast is approved")
        self.route = route
        self.fields = dict(policy["contract_fields"])
        self.db = sqlite3.connect(":memory:")
        self.db.execute("""CREATE TABLE manifest (
            tenant TEXT, dataset TEXT, bucket TEXT, object_key TEXT,
            version_id TEXT, checksum TEXT NOT NULL,
            PRIMARY KEY (tenant, dataset, bucket, object_key, version_id))""")
        self.db.execute("""CREATE TABLE bronze (
            tenant TEXT, dataset TEXT, bucket TEXT, object_key TEXT,
            version_id TEXT, line_number INTEGER, row_json TEXT NOT NULL,
            repaired INTEGER NOT NULL, repair_rule TEXT,
            PRIMARY KEY (tenant, dataset, bucket, object_key, version_id, line_number))""")
        self.db.execute("""CREATE TABLE quarantine (
            tenant TEXT, dataset TEXT, bucket TEXT, object_key TEXT,
            version_id TEXT, line_number INTEGER, reason TEXT NOT NULL,
            raw_line TEXT NOT NULL,
            PRIMARY KEY (tenant, dataset, bucket, object_key, version_id, line_number))""")
        self.db.execute("""CREATE TABLE held (
            tenant TEXT, dataset TEXT, bucket TEXT, object_key TEXT,
            version_id TEXT, checksum TEXT NOT NULL, body BLOB NOT NULL,
            review_json TEXT NOT NULL,
            PRIMARY KEY (tenant, dataset, bucket, object_key, version_id))""")

    def _validate_batch(self, batch: ObjectBatch) -> None:
        if batch.tenant != self.route["tenant_id"] or batch.dataset != self.route["name"]:
            raise ValueError("Object does not belong to this tenant route")
        if not batch.version_id or batch.version_id == "null":
            raise ValueError("A non-null object version ID is required")
        prefix = self.route["source"]["prefix"]
        expected_bucket, expected_prefix = prefix[5:].split("/", 1)
        if batch.bucket != expected_bucket or not batch.key.startswith(expected_prefix):
            raise ValueError("Object is outside the configured tenant prefix")

    def _normalise(self, row: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None, bool]:
        missing = self.fields.keys() - row.keys()
        if missing:
            return None, f"missing_{sorted(missing)[0]}", False
        if isinstance(row["order_id"], bool) or not isinstance(row["order_id"], int):
            return None, "invalid_order_id", False
        if not isinstance(row["status"], str) or row["status"] not in {"paid", "pending"}:
            return None, "invalid_status", False
        amount = row["amount"]
        repaired = isinstance(amount, str)
        if isinstance(amount, bool) or not isinstance(amount, (int, float, str)):
            return None, "invalid_amount", False
        if repaired and not DECIMAL_2.fullmatch(amount):
            return None, "invalid_amount", False
        try:
            decimal = Decimal(str(amount))
            if not decimal.is_finite() or decimal.as_tuple().exponent < -2:
                return None, "invalid_amount", False
            value = f"{decimal:.2f}"
        except (InvalidOperation, ValueError):
            return None, "invalid_amount", False
        return {"order_id": row["order_id"], "amount": value,
                "status": row["status"]}, None, repaired

    def process(self, batch: ObjectBatch) -> dict[str, Any]:
        self._validate_batch(batch)
        identity = batch.identity
        with self.db:
            committed = self.db.execute("""SELECT checksum FROM manifest WHERE
                tenant=? AND dataset=? AND bucket=? AND object_key=? AND version_id=?""",
                identity).fetchone()
            if committed:
                if committed[0] != batch.checksum:
                    raise ValueError("Same object version has conflicting content")
                return {"status": "duplicate_noop"}
            held = self.db.execute("""SELECT checksum FROM held WHERE
                tenant=? AND dataset=? AND bucket=? AND object_key=? AND version_id=?""",
                identity).fetchone()
            if held and held[0] != batch.checksum:
                raise ValueError("Held object version has conflicting content")
            if held:
                packet = self.review_packet(batch)
                return {"status": "held_for_review", "schema_diff": packet["schema_diff"]}

            decoded = batch.body.decode("utf-8")
            lines = decoded.splitlines()
            parsed: list[tuple[int, str, dict[str, Any] | None]] = []
            changes: dict[str, str] = {}
            for line_number, raw_line in enumerate(lines, 1):
                try:
                    row = json.loads(raw_line)
                except json.JSONDecodeError:
                    row = None
                if isinstance(row, dict):
                    for name, value in row.items():
                        if name not in self.fields:
                            changes[name] = field_type(value)
                else:
                    row = None
                parsed.append((line_number, raw_line, row))

            if changes:
                packet = {"tenant": batch.tenant, "dataset": batch.dataset,
                          "contract": self.route["contract"],
                          "schema_diff": [{"field": name, "type": kind, "change": "added"}
                                          for name, kind in sorted(changes.items())],
                          "instruction": "Suggest classification and mapping; never approve or ingest."}
                self.db.execute("""INSERT OR REPLACE INTO held VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                                (*identity, batch.checksum, batch.body, json.dumps(packet)))
                return {"status": "held_for_review", "schema_diff": packet["schema_diff"]}

            repaired_count = landed_count = quarantined_count = 0
            for line_number, raw_line, row in parsed:
                if row is None:
                    cleaned, reason, repaired = None, "invalid_json", False
                else:
                    cleaned, reason, repaired = self._normalise(row)
                if cleaned is None:
                    self.db.execute("INSERT INTO quarantine VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                    (*identity, line_number, reason, raw_line))
                    quarantined_count += 1
                else:
                    self.db.execute("INSERT INTO bronze VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                    (*identity, line_number, json.dumps(cleaned), int(repaired),
                                     "exact_decimal_cast" if repaired else None))
                    landed_count += 1
                    repaired_count += int(repaired)
            self.db.execute("INSERT INTO manifest VALUES (?, ?, ?, ?, ?, ?)",
                            (*identity, batch.checksum))
            self.db.execute("""DELETE FROM held WHERE tenant=? AND dataset=? AND bucket=?
                AND object_key=? AND version_id=?""", identity)
            return {"status": "committed", "landed": landed_count,
                    "repaired": repaired_count, "quarantined": quarantined_count}

    def review_packet(self, batch: ObjectBatch) -> dict[str, Any]:
        row = self.db.execute("""SELECT review_json FROM held WHERE tenant=? AND dataset=?
            AND bucket=? AND object_key=? AND version_id=?""", batch.identity).fetchone()
        if row is None:
            raise ValueError("No held file with this identity")
        return json.loads(row[0])

    def counts(self) -> tuple[int, int, int]:
        return tuple(self.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                     for table in ("manifest", "bronze", "quarantine"))


def request_ai_suggestion(packet: dict[str, Any],
                          provider: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
    allowed = {"tenant", "dataset", "contract", "schema_diff", "instruction"}
    if set(packet) != allowed:
        raise ValueError("Unexpected data in AI review packet")
    return {"suggestion": provider(packet), "requires_human_approval": True}


def main() -> None:
    guard = FileGuardrails(load_route("beacon", "orders"))
    first = ObjectBatch("beacon", "orders", "beacon-inbox", "orders/day-01.json",
                        "v17", b'{"order_id":1,"amount":"19.50","status":"paid"}\n'
                               b'{"order_id":2,"amount":"oops","status":"paid"}\n'
                               b'{"order_id":3,"amount":12,"status":"pending"}\n')
    assert guard.process(first) == {"status": "committed", "landed": 2,
                                    "repaired": 1, "quarantined": 1}
    assert guard.process(first) == {"status": "duplicate_noop"}
    assert guard.counts() == (1, 2, 1)
    repaired_row, repair_rule = guard.db.execute(
        "SELECT row_json, repair_rule FROM bronze WHERE line_number=1").fetchone()
    assert json.loads(repaired_row)["amount"] == "19.50"
    assert repair_rule == "exact_decimal_cast"
    assert guard.db.execute("SELECT reason FROM quarantine").fetchone()[0] == "invalid_amount"
    conflicting = ObjectBatch("beacon", "orders", "beacon-inbox", "orders/day-01.json",
                              "v17", b'{"order_id":1,"amount":"20.00","status":"paid"}\n')
    try:
        guard.process(conflicting)
    except ValueError as exc:
        assert "conflicting content" in str(exc)
    else:
        raise AssertionError("Conflicting object content was silently accepted")

    drifted = ObjectBatch("beacon", "orders", "beacon-inbox", "orders/day-02.json",
                          "v18", b'{"order_id":4,"amount":"27.00","status":"paid",'
                                 b'"customer_phone":"07123456789"}\n')
    assert guard.process(drifted)["status"] == "held_for_review"
    assert guard.process(drifted)["status"] == "held_for_review"
    packet = guard.review_packet(drifted)
    assert "07123456789" not in json.dumps(packet)
    advisory = request_ai_suggestion(packet, lambda _: {
        "classification": "personal", "action": "review necessity and tokenisation"})
    assert advisory["requires_human_approval"]
    assert guard.counts() == (1, 2, 1)
    print("file v17: 1 exact repair, 1 quarantine, 2 landed")
    print("same object version: duplicate no-op; conflicting content: rejected")
    print("file v18: new field held; mock AI advice requires review")
    print(json.dumps(advisory, indent=2))


if __name__ == "__main__":
    main()
