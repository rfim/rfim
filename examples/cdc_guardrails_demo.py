"""Runnable synthetic CDC guardrails reference using the shared tenant YAML.

This is a local SQLite simulation of idempotent CDC effects and schema/privacy
gates, not a Debezium or Delta deployment. AI receives schema metadata only;
the mock suggestion in main() never approves a contract change.

Run: pip install -r examples/requirements.txt
     python examples/cdc_guardrails_demo.py
"""

from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

import yaml

CONFIG = Path(__file__).with_name("multitenant-ingestion.yaml")


@dataclass(frozen=True)
class CDCEvent:
    tenant: str
    dataset: str
    source: str
    table: str
    lsn: int
    transaction_id: str
    event_order: int
    primary_key: str
    op: str
    after: dict[str, Any]

    @property
    def event_id(self) -> str:
        parts = (self.tenant, self.dataset, self.source, self.table,
                 self.lsn, self.transaction_id, self.event_order, self.primary_key)
        return hashlib.sha256(json.dumps(parts).encode()).hexdigest()


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
    if value is None:
        return "null"
    return type(value).__name__


class CDCGuardrails:
    def __init__(self, route: dict[str, Any], token_key: bytes):
        if not token_key:
            raise ValueError("A token key is required for personal fields")
        self.route = route
        self.token_key = token_key
        self.contract_fields = dict(route["cdc"]["contract_fields"])
        self.approved_fields = set(route["privacy"]["approved_fields"])
        if route["cdc"]["auto_evolve"] or route["privacy"]["ai_advisory"]["auto_approve"]:
            raise ValueError("Schema evolution and AI approval must remain reviewed")
        if route["privacy"]["ai_advisory"]["input"] != "schema_metadata_only":
            raise ValueError("AI input must be restricted to schema metadata")
        self.personal_fields: set[str] = set()
        self.db = sqlite3.connect(":memory:")
        self.db.execute("""CREATE TABLE seen (
            event_id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL,
            result TEXT NOT NULL)""")
        self.db.execute("""CREATE TABLE entities (
            tenant TEXT NOT NULL, dataset TEXT NOT NULL, entity_key TEXT NOT NULL,
            lsn INTEGER NOT NULL, event_order INTEGER NOT NULL,
            deleted INTEGER NOT NULL, data_json TEXT NOT NULL,
            PRIMARY KEY (tenant, dataset, entity_key))""")
        self.db.execute("""CREATE TABLE held (
            event_id TEXT PRIMARY KEY, event_json TEXT NOT NULL,
            review_json TEXT NOT NULL)""")

    def _validate_route(self, event: CDCEvent) -> None:
        if (event.tenant != self.route["tenant_id"] or event.dataset != self.route["name"] or
                event.source != "postgres_cdc" or
                event.table != self.route["source"]["table"]):
            raise ValueError("Event does not match the configured tenant route")
        if event.op not in {"c", "u", "d"}:
            raise ValueError("Only streaming create/update/delete events are supported")
        if event.lsn < 0 or event.event_order < 0 or not event.primary_key:
            raise ValueError("Missing stable CDC identity or ordering metadata")
        primary_key_field = self.route["cdc"]["primary_key"]
        if event.op != "d" and str(event.after.get(primary_key_field)) != event.primary_key:
            raise ValueError("CDC key differs from the configured row key")

    def _schema_diff(self, event: CDCEvent) -> list[dict[str, str]]:
        if event.op == "d":
            return []
        changes = []
        for name, value in event.after.items():
            observed = field_type(value)
            expected = self.contract_fields.get(name)
            if expected is None:
                changes.append({"field": name, "change": "added", "type": observed})
            elif expected != observed and not (expected == "number" and observed == "integer"):
                changes.append({"field": name, "change": "type_changed",
                                "from": expected, "to": observed})
            elif name not in self.approved_fields:
                changes.append({"field": name, "change": "not_approved", "type": observed})
        for name in self.contract_fields.keys() - event.after.keys():
            changes.append({"field": name, "change": "missing",
                            "expected_type": self.contract_fields[name]})
        return sorted(changes, key=lambda item: item["field"])

    def _review_packet(self, event: CDCEvent, changes: list[dict[str, str]]) -> dict[str, Any]:
        # No row values, raw samples, email addresses, or secret values enter this packet.
        return {"tenant": event.tenant, "dataset": event.dataset,
                "contract": self.route["contract"],
                "purpose": self.route["privacy"]["purpose"],
                "schema_diff": changes,
                "instruction": "Suggest classification and migration; never approve or ingest."}

    def review_packet(self, event_id: str) -> dict[str, Any]:
        row = self.db.execute("SELECT review_json FROM held WHERE event_id=?", (event_id,)).fetchone()
        if row is None:
            raise ValueError("No held event with this identity")
        return json.loads(row[0])

    def process(self, event: CDCEvent) -> str:
        self._validate_route(event)
        payload_hash = hashlib.sha256(json.dumps(asdict(event), sort_keys=True).encode()).hexdigest()
        with self.db:
            seen = self.db.execute("SELECT payload_hash FROM seen WHERE event_id=?",
                                   (event.event_id,)).fetchone()
            if seen:
                if seen[0] != payload_hash:
                    raise ValueError("Conflicting content for the same CDC event identity")
                return "duplicate_noop"
            held = self.db.execute("SELECT event_json FROM held WHERE event_id=?",
                                   (event.event_id,)).fetchone()
            if held and json.loads(held[0]) != asdict(event):
                raise ValueError("Conflicting held content for the same CDC event identity")

            current = self.db.execute(
                "SELECT lsn, event_order FROM entities WHERE tenant=? AND dataset=? AND entity_key=?",
                (event.tenant, event.dataset, event.primary_key)).fetchone()
            if current and (event.lsn, event.event_order) <= current:
                self.db.execute("INSERT INTO seen VALUES (?, ?, ?)",
                                (event.event_id, payload_hash, "stale_noop"))
                self.db.execute("DELETE FROM held WHERE event_id=?", (event.event_id,))
                return "stale_noop"

            changes = self._schema_diff(event)
            if changes:
                packet = self._review_packet(event, changes)
                self.db.execute("INSERT OR REPLACE INTO held VALUES (?, ?, ?)",
                                (event.event_id, json.dumps(asdict(event)), json.dumps(packet)))
                return "held_for_review"

            data = dict(event.after)
            for field in self.personal_fields & data.keys():
                value = str(data[field]).encode()
                data[field] = hmac.new(self.token_key, value, hashlib.sha256).hexdigest()
            deleted = int(event.op == "d")
            if deleted:
                data = {}
            self.db.execute("""INSERT INTO entities VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(tenant, dataset, entity_key) DO UPDATE SET
                lsn=excluded.lsn, event_order=excluded.event_order,
                deleted=excluded.deleted, data_json=excluded.data_json""",
                (event.tenant, event.dataset, event.primary_key, event.lsn,
                 event.event_order, deleted, json.dumps(data)))
            self.db.execute("INSERT INTO seen VALUES (?, ?, ?)",
                            (event.event_id, payload_hash, "applied"))
            self.db.execute("DELETE FROM held WHERE event_id=?", (event.event_id,))
            return "applied"

    def approve_field(self, name: str, kind: str, classification: str) -> None:
        """Explicit reviewer action; never called by the AI suggestion provider."""
        if classification not in {"operational", "personal"}:
            raise ValueError("Reviewer must choose an allowed classification")
        self.contract_fields[name] = kind
        self.approved_fields.add(name)
        if classification == "personal":
            self.personal_fields.add(name)

    def replay_held(self, event_id: str) -> str:
        row = self.db.execute("SELECT event_json FROM held WHERE event_id=?", (event_id,)).fetchone()
        if row is None:
            raise ValueError("No held event with this identity")
        return self.process(CDCEvent(**json.loads(row[0])))

    def entity(self, key: str) -> tuple[int, int, bool, dict[str, Any]] | None:
        row = self.db.execute("""SELECT lsn, event_order, deleted, data_json FROM entities
            WHERE tenant=? AND dataset=? AND entity_key=?""",
            (self.route["tenant_id"], self.route["name"], key)).fetchone()
        return (row[0], row[1], bool(row[2]), json.loads(row[3])) if row else None


def request_ai_suggestion(packet: dict[str, Any], provider: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
    """Integration point: a real provider can see metadata and return advice only."""
    allowed = {"tenant", "dataset", "contract", "purpose", "schema_diff", "instruction"}
    if set(packet) != allowed:
        raise ValueError("Unexpected data in AI review packet")
    suggestion = provider(packet)
    return {"suggestion": suggestion, "requires_human_approval": True}


def main() -> None:
    guard = CDCGuardrails(load_route("aurora", "orders"), b"synthetic-demo-key")
    first = CDCEvent("aurora", "orders", "postgres_cdc", "public.orders",
                     2048, "tx-71", 1, "42", "u",
                     {"id": 42, "amount": 99, "status": "paid"})
    assert guard.process(first) == "applied"
    assert guard.process(first) == "duplicate_noop"
    conflicting = CDCEvent("aurora", "orders", "postgres_cdc", "public.orders",
                           2048, "tx-71", 1, "42", "u",
                           {"id": 42, "amount": 100, "status": "paid"})
    try:
        guard.process(conflicting)
    except ValueError as exc:
        assert "Conflicting content" in str(exc)
    else:
        raise AssertionError("Conflicting CDC content was silently accepted")
    stale = CDCEvent("aurora", "orders", "postgres_cdc", "public.orders",
                     2047, "tx-70", 1, "42", "u",
                     {"id": 42, "amount": 80, "status": "pending"})
    assert guard.process(stale) == "stale_noop"
    type_changed = CDCEvent("aurora", "orders", "postgres_cdc", "public.orders",
                            2049, "tx-71b", 1, "42", "u",
                            {"id": 42, "amount": "99", "status": "paid"})
    assert guard.process(type_changed) == "held_for_review"
    assert guard.review_packet(type_changed.event_id)["schema_diff"][0]["change"] == "type_changed"

    changed = CDCEvent("aurora", "orders", "postgres_cdc", "public.orders",
                       2051, "tx-72", 1, "42", "u",
                       {"id": 42, "amount": 99, "status": "paid",
                        "customer_phone": "07123456789"})
    assert guard.process(changed) == "held_for_review"
    assert guard.process(changed) == "held_for_review"
    conflicting_held = CDCEvent("aurora", "orders", "postgres_cdc", "public.orders",
                                2051, "tx-72", 1, "42", "u",
                                {"id": 42, "amount": 99, "status": "paid",
                                 "customer_phone": "07999999999"})
    try:
        guard.process(conflicting_held)
    except ValueError as exc:
        assert "Conflicting held content" in str(exc)
    else:
        raise AssertionError("Conflicting held CDC content was silently accepted")
    packet = guard.review_packet(changed.event_id)
    assert "07123456789" not in json.dumps(packet)
    advisory = request_ai_suggestion(packet, lambda _: {
        "classification": "personal", "migration": "tokenise before curated use"})
    assert advisory["requires_human_approval"]
    # Simulated reviewer approves a contract v2 change, then replays the held row.
    guard.approve_field("customer_phone", "string", "personal")
    assert guard.replay_held(changed.event_id) == "applied"
    assert guard.entity("42")[3]["customer_phone"] != "07123456789"

    deleted = CDCEvent("aurora", "orders", "postgres_cdc", "public.orders",
                       2052, "tx-73", 1, "42", "d", {})
    assert guard.process(deleted) == "applied"
    assert guard.process(changed) == "duplicate_noop"
    assert guard.entity("42")[2] is True  # tombstone blocks older resurrection
    print("applied > duplicate no-op > stale no-op > type drift hold > AI advice")
    print("reviewed contract change > tokenised replay > delete tombstone")
    print(json.dumps(advisory, indent=2))


if __name__ == "__main__":
    main()
