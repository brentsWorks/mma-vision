"""Tests for the transition grammar (P1.2).

These pin grammar.yaml to docs/ontology.md §3 and lock in the SOFT-grammar invariants
the decoder (P1.4) relies on: costs are finite, ordered, and SCRAMBLE is the universal
low-cost release valve.
"""

import pytest

from mma_vision.ontology.grammar import Grammar, load_grammar


def test_loads_and_matches_ontology_version():
    g = load_grammar()
    assert g.version == "0.1.0"


def test_cost_ordering():
    # docs/ontology.md §3: self < direct < rare < forbidden-via-scramble.
    g = load_grammar()
    assert g.costs["self"] < g.costs["direct"] < g.costs["rare"] < g.costs["forbidden_via_scramble"]
    assert g.costs["self"] == 0.0


def test_self_transition_is_free():
    g = load_grammar()
    assert g.ground_cost("G-MOUNT", "G-MOUNT") == 0.0
    assert g.regime_cost("R-GROUND", "R-GROUND") == 0.0


def test_mount_to_guard_is_forbidden_via_scramble():
    # The signature design choice: a sweep is definitionally a scramble (docs §3).
    g = load_grammar()
    assert g.ground_cost("G-MOUNT", "G-GUARD") == g.costs["forbidden_via_scramble"]


def test_guard_to_mount_forbidden_but_guard_to_back_merely_rare():
    # Encodes real grappling asymmetry (docs/ontology.md §3).
    g = load_grammar()
    assert g.ground_cost("G-GUARD", "G-MOUNT") == g.costs["forbidden_via_scramble"]
    assert g.ground_cost("G-GUARD", "G-BACK") == g.costs["rare"]


def test_scramble_is_cheap_from_everywhere():
    # X-SCRAMBLE is the low-cost pressure-release valve, reachable direct (docs §3).
    g = load_grammar()
    for src in ("G-GUARD", "G-HALF", "G-SIDE", "G-NS", "G-MOUNT", "G-BACK", "G-TURTLE"):
        assert g.ground_cost(src, "X-SCRAMBLE") == g.costs["direct"]
        assert g.ground_cost("X-SCRAMBLE", src) == g.costs["direct"]


def test_turtle_connects_cheaply_to_everything():
    # The great branching point (docs/ontology.md §3): every TURTLE exit is direct.
    g = load_grammar()
    for dst in ("G-GUARD", "G-HALF", "G-SIDE", "G-NS", "G-BACK"):
        assert g.ground_cost("G-TURTLE", dst) == g.costs["direct"]


def test_no_infinite_costs_grammar_is_soft():
    # The whole grammar must be finite so the decoder lattice never goes undecodable.
    g = load_grammar()
    assert all(c != float("inf") for c in g.costs.values())


def test_offmatrix_pair_routes_through_scramble():
    # X-SEPARATED has no from-row; its cost must be the SCRAMBLE detour, not an error.
    g = load_grammar()
    detour = g.ground_cost("X-SEPARATED", "G-GUARD")
    expected = g.ground_cost("X-SEPARATED", "X-SCRAMBLE") + g.ground_cost("X-SCRAMBLE", "G-GUARD")
    # The detour both succeeds and equals routing through SCRAMBLE.
    assert detour == expected
    assert detour == g.costs["direct"] + g.costs["direct"]


def test_regime_stand_ground_forbidden_via_scramble():
    # There is always an R-TRANS between standing and ground (docs/ontology.md §3).
    g = load_grammar()
    assert g.regime_cost("R-STAND", "R-GROUND") == g.costs["forbidden_via_scramble"]
    assert g.regime_cost("R-GROUND", "R-STAND") == g.costs["forbidden_via_scramble"]
    assert g.regime_cost("R-STAND", "R-CLINCH") == g.costs["direct"]


def test_rejects_version_mismatch():
    bad = {
        "version": "9.9.9",
        "costs": {"self": 0.0, "direct": 1.0},
        "ground_matrix": {},
        "regime_matrix": {},
    }
    with pytest.raises(ValueError, match="version"):
        Grammar.model_validate(bad)


def test_rejects_unknown_state_in_matrix():
    bad = {
        "version": "0.1.0",
        "costs": {"self": 0.0, "direct": 1.0},
        "ground_matrix": {"G-NOPE": {"G-GUARD": "direct"}},
        "regime_matrix": {},
    }
    with pytest.raises(ValueError, match="unknown state"):
        Grammar.model_validate(bad)


def test_rejects_unknown_cost_code():
    bad = {
        "version": "0.1.0",
        "costs": {"self": 0.0, "direct": 1.0},
        "ground_matrix": {"G-GUARD": {"G-HALF": "teleport"}},
        "regime_matrix": {},
    }
    with pytest.raises(ValueError, match="unknown cost code"):
        Grammar.model_validate(bad)
