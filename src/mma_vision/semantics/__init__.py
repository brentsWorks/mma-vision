"""Semantic layer.

Grammar-constrained Viterbi/beam decode over per-frame state distributions, plus
event derivation from state transitions (a sweep IS a top/bottom inversion via
scramble). See DESIGN.md §2 and docs/ontology.md §4.
"""
