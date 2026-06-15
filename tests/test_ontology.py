"""Tests for the ontology spec (P1.1).

These pin the ontology to docs/ontology.md so drift between the prose spec and the
machine-readable source is caught.
"""

import pytest

from mma_vision.ontology.spec import Ontology, load_ontology


def test_loads_and_validates():
    ont = load_ontology()
    assert ont.version == "0.1.0"


def test_tier1_state_inventory():
    # docs/ontology.md §2: 3 standing + 3 clinch + 7 ground + 2 universal = 15.
    ont = load_ontology()
    assert len(ont.states) == 15
    ground = [s for s in ont.states if s.regime == "R-GROUND"]
    assert len(ground) == 7


def test_all_four_regimes_present():
    ont = load_ontology()
    assert {r.id for r in ont.regimes} == {"R-STAND", "R-CLINCH", "R-GROUND", "R-TRANS"}


def test_dual_indexing():
    # Ground states are relational: top != bottom label.
    ont = load_ontology()
    mount = ont.state("G-MOUNT")
    assert mount.dual.a == "mount-top"
    assert mount.dual.b == "mounted"
    assert not mount.symmetric
    # Standing-open is symmetric.
    assert ont.state("S-OPEN").symmetric


def test_dominance_partial_order():
    # The grappling advancement ladder must increase in dominance.
    ont = load_ontology()
    ladder = ["G-GUARD", "G-HALF", "G-SIDE", "G-MOUNT", "G-BACK"]
    doms = [ont.dominance_of(s) for s in ladder]
    assert doms == sorted(doms), "dominance must be non-decreasing up the ladder"
    assert ont.dominance_of("G-BACK") > ont.dominance_of("G-GUARD")


def test_scramble_has_no_dominance():
    ont = load_ontology()
    assert ont.dominance_of("X-SCRAMBLE") == 0.0


def test_collapse_tier2_to_tier1():
    ont = load_ontology()
    assert ont.collapse_to_tier1("G-BACK-BODY-TRIANGLE") == "G-BACK"
    assert ont.collapse_to_tier1("G-MOUNT") == "G-MOUNT"  # already Tier-1


def test_known_gaps_recorded():
    # The leg-entanglement gap must stay visible in-spec (docs/ontology.md §5).
    ont = load_ontology()
    gap_ids = {g.id for g in ont.known_gaps}
    assert "G-NEUTRAL-GROUND" in gap_ids


def test_rejects_unknown_regime_reference():
    bad = {
        "version": "x",
        "dominance_scale": {"low": 0.2},
        "regimes": [{"id": "R-STAND", "name": "S", "desc": "d"}],
        "states": [
            {
                "id": "BAD",
                "regime": "R-NOPE",
                "name": "bad",
                "dual": {"a": "x", "b": "y"},
                "symmetric": True,
            }
        ],
    }
    with pytest.raises(ValueError, match="unknown regime"):
        Ontology.model_validate(bad)
