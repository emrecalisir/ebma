from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Atom:
    """Typed CBM atom: (event_key ∧ attr ∧ numeric_bin)."""

    event_key: str
    attr: str
    numeric: str
    op: str
    threshold: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_key": self.event_key,
            "attr": self.attr,
            "numeric": self.numeric,
            "op": self.op,
            "threshold": float(self.threshold),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Atom":
        return cls(d["event_key"], d["attr"], d["numeric"], d["op"], float(d["threshold"]))


@dataclass
class Audience:
    audience_id: str
    arm: str
    atoms: list[Atom]
    combine: str = "or"
    text_tag: str | None = None
    notes: dict[str, Any] = field(default_factory=dict)
    code_path_id: str = ""

    def to_ast(self) -> dict[str, Any]:
        return {
            "audience_id": self.audience_id,
            "arm": self.arm,
            "combine": self.combine,
            "atoms": [a.to_dict() for a in self.atoms],
            "text_tag": self.text_tag,
            "language": "L_typed_cbm_v1",
            "code_path_id": self.code_path_id,
        }
