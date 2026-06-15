"""Typed loader + validator for the position ontology.

Single source of truth is ``ontology.yaml`` (sibling file). This module loads it,
validates structure and cross-references with pydantic, and exposes typed lookups
used by the decoder (P1.4), the annotation tool (P3.x), and the eval harness (P4.x).

Validation here is deliberately strict: a malformed ontology should fail loudly at
load time, not silently produce wrong labels downstream.
"""

from __future__ import annotations

from functools import lru_cache
from importlib import resources

import yaml
from pydantic import BaseModel, Field, model_validator

_ONTOLOGY_FILE = "ontology.yaml"


class Dual(BaseModel):
    """Per-fighter labels for one physical configuration (states are relational)."""

    a: str
    b: str


class Regime(BaseModel):
    id: str
    name: str
    desc: str


class State(BaseModel):
    id: str
    regime: str
    name: str
    dual: Dual
    symmetric: bool
    # Dominance key into ``dominance_scale``; only meaningful for ground states.
    dominance: str | None = None


class SubPosition(BaseModel):
    id: str
    parent: str
    name: str


class Event(BaseModel):
    id: str
    params: list[str] = Field(default_factory=list)


class KnownGap(BaseModel):
    id: str
    note: str


class Ontology(BaseModel):
    """The validated ontology. Build via :func:`load_ontology`."""

    version: str
    dominance_scale: dict[str, float]
    regimes: list[Regime]
    states: list[State]
    sub_positions: list[SubPosition] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    known_gaps: list[KnownGap] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_cross_references(self) -> Ontology:
        regime_ids = {r.id for r in self.regimes}
        state_ids = {s.id for s in self.states}

        # Every state's regime must exist.
        for s in self.states:
            if s.regime not in regime_ids:
                raise ValueError(f"state {s.id!r} references unknown regime {s.regime!r}")
            # Dominance key, if present, must exist in the scale.
            if s.dominance is not None and s.dominance not in self.dominance_scale:
                raise ValueError(f"state {s.id!r} references unknown dominance {s.dominance!r}")

        # Sub-positions must point at a real Tier-1 state.
        for sub in self.sub_positions:
            if sub.parent not in state_ids:
                raise ValueError(
                    f"sub_position {sub.id!r} references unknown parent {sub.parent!r}"
                )

        # No duplicate ids anywhere they would collide.
        _no_dupes("regime", [r.id for r in self.regimes])
        _no_dupes("state", [s.id for s in self.states])
        _no_dupes("sub_position", [s.id for s in self.sub_positions])
        _no_dupes("event", [e.id for e in self.events])
        return self

    # -- convenience lookups -------------------------------------------------

    def state(self, state_id: str) -> State:
        for s in self.states:
            if s.id == state_id:
                return s
        raise KeyError(state_id)

    def state_ids(self) -> list[str]:
        return [s.id for s in self.states]

    def dominance_of(self, state_id: str) -> float:
        """Normalized top-fighter dominance for a state (0.0 if undefined)."""
        dom = self.state(state_id).dominance
        return self.dominance_scale[dom] if dom else 0.0

    def collapse_to_tier1(self, position_id: str) -> str:
        """Map a Tier-2 sub-position id up to its Tier-1 parent; pass through Tier-1."""
        for sub in self.sub_positions:
            if sub.id == position_id:
                return sub.parent
        return position_id  # already Tier-1 (or unknown — caller validates)


def _no_dupes(kind: str, ids: list[str]) -> None:
    seen: set[str] = set()
    for i in ids:
        if i in seen:
            raise ValueError(f"duplicate {kind} id {i!r}")
        seen.add(i)


@lru_cache(maxsize=1)
def load_ontology() -> Ontology:
    """Load and validate the bundled ontology (cached)."""
    text = resources.files(__package__).joinpath(_ONTOLOGY_FILE).read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    return Ontology.model_validate(data)
