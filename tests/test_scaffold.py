"""Smoke test: the package imports and its subsystems are present.

Trivial by design — P0.0's DONE condition is 'repo installs clean and a trivial
test passes'. Real tests arrive with each backlog item.
"""

import importlib

import mma_vision


def test_version():
    assert mma_vision.__version__ == "0.0.1"


def test_subsystems_importable():
    # The package layout mirrors the architecture seams (DESIGN.md §7).
    for sub in (
        "ingest",
        "perception",
        "fightgraph",
        "ontology",
        "semantics",
        "rig",
        "annotation",
        "eval",
        "api",
        "views",
    ):
        importlib.import_module(f"mma_vision.{sub}")
