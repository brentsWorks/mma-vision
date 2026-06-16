"""Typed loader + validator for the transition grammar (P1.2).

Single source of truth is ``grammar.yaml`` (sibling file), mirroring docs/ontology.md §3.
This module loads it, resolves the symbolic cost codes (``direct``/``rare``/…) to numeric
penalties, cross-validates every state/regime id against the ontology (P1.1), and exposes
the ``cost(from, to)`` lookups the constrained decoder (P1.4) needs.

The grammar is SOFT: ``cost`` always returns a finite number. There is no "illegal"
transition — only an expensive one — so the Viterbi/beam lattice in P1.4 can never become
undecodable (no ``-inf`` edges), which is what lets the decoder recover from genuinely fast
scrambles and dropped frames.
"""

from __future__ import annotations

from functools import lru_cache
from importlib import resources

import yaml
from pydantic import BaseModel, PrivateAttr, model_validator

from mma_vision.ontology.spec import load_ontology

_GRAMMAR_FILE = "grammar.yaml"

# Ground states the matrix ranges over (docs/ontology.md §3). The universal states
# X-SCRAMBLE / X-SEPARATED participate as columns (and SCRAMBLE as a row) but the
# matrix is intentionally NOT defined for X-SEPARATED as a from-row: a fighter
# separating leads back to standing, which is regime-level, not ground-level.
_GROUND_FROM = (
    "G-GUARD",
    "G-HALF",
    "G-SIDE",
    "G-NS",
    "G-MOUNT",
    "G-BACK",
    "G-TURTLE",
    "X-SCRAMBLE",
)
_GROUND_TO = _GROUND_FROM + ("X-SEPARATED",)

# The release-valve state. Any ground pair missing from the matrix is costed as
# "route through SCRAMBLE" (from→SCRAMBLE then SCRAMBLE→to) rather than being an error.
_SCRAMBLE = "X-SCRAMBLE"


class Grammar(BaseModel):
    """The validated transition grammar. Build via :func:`load_grammar`."""

    version: str
    costs: dict[str, float]
    ground_matrix: dict[str, dict[str, str]]
    regime_matrix: dict[str, dict[str, str]]

    # Filled in during validation: symbolic codes resolved to numbers.
    _ground_cost: dict[tuple[str, str], float] = PrivateAttr(default_factory=dict)
    _regime_cost: dict[tuple[str, str], float] = PrivateAttr(default_factory=dict)

    @model_validator(mode="after")
    def _resolve_and_check(self) -> Grammar:
        ont = load_ontology()
        if self.version != ont.version:
            raise ValueError(
                f"grammar version {self.version!r} != ontology version {ont.version!r}"
            )

        state_ids = set(ont.state_ids())
        regime_ids = {r.id for r in ont.regimes}

        self._ground_cost = self._resolve_matrix(
            self.ground_matrix, _GROUND_FROM, _GROUND_TO, state_ids, "state"
        )
        self._regime_cost = self._resolve_matrix(
            self.regime_matrix,
            tuple(regime_ids),
            tuple(regime_ids),
            regime_ids,
            "regime",
        )
        return self

    def _resolve_matrix(
        self,
        matrix: dict[str, dict[str, str]],
        from_keys: tuple[str, ...],
        to_keys: tuple[str, ...],
        valid_ids: set[str],
        kind: str,
    ) -> dict[tuple[str, str], float]:
        resolved: dict[tuple[str, str], float] = {}
        for src, row in matrix.items():
            if src not in valid_ids:
                raise ValueError(f"grammar references unknown {kind} {src!r} (from-row)")
            if src not in from_keys:
                raise ValueError(f"unexpected {kind} from-row {src!r} in grammar")
            for dst, code in row.items():
                if dst not in valid_ids:
                    raise ValueError(f"grammar references unknown {kind} {dst!r} (to-column)")
                if dst not in to_keys:
                    raise ValueError(f"unexpected {kind} to-column {dst!r} in grammar")
                if code not in self.costs:
                    raise ValueError(f"transition {src!r}->{dst!r} uses unknown cost code {code!r}")
                resolved[(src, dst)] = self.costs[code]
        return resolved

    # -- cost lookups --------------------------------------------------------

    def ground_cost(self, src: str, dst: str) -> float:
        """Transition cost between two ground/universal states.

        For any pair not explicitly in the matrix (e.g. X-SEPARATED as a source),
        the cost is the SCRAMBLE detour ``src→SCRAMBLE + SCRAMBLE→dst`` — the grammar's
        pressure-release path — never an error. Self-transitions are free.
        """
        if src == dst:
            return self.costs["self"]
        direct = self._ground_cost.get((src, dst))
        if direct is not None:
            return direct
        # Route through the release valve. Each leg falls back to a single hop's
        # cost if even that leg is unlisted (defensive; both legs are normally present).
        to_scramble = self._ground_cost.get((src, _SCRAMBLE), self.costs["direct"])
        from_scramble = self._ground_cost.get((_SCRAMBLE, dst), self.costs["direct"])
        return to_scramble + from_scramble

    def regime_cost(self, src: str, dst: str) -> float:
        """Transition cost between two Tier-0 regimes."""
        if src == dst:
            return self.costs["self"]
        cost = self._regime_cost.get((src, dst))
        if cost is None:
            raise KeyError(f"no regime transition defined {src!r}->{dst!r}")
        return cost


@lru_cache(maxsize=1)
def load_grammar() -> Grammar:
    """Load and validate the bundled grammar against the ontology (cached)."""
    text = resources.files(__package__).joinpath(_GRAMMAR_FILE).read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    return Grammar.model_validate(data)
