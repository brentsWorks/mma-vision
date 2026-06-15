"""MMA computer vision analysis.

Core thesis: this is a *relational-state-estimation* problem where tracking is a
(sometimes unsolvable) sub-task — not a tracking problem with a semantics layer on
top. See DESIGN.md.

Subsystem layout mirrors the architecture seams (DESIGN.md §7):

    ingest      -> shot-boundary / camera-regime gate
    perception  -> regime, identity-memory, keypoints, contact topology
    fightgraph  -> the per-frame structured representation (the key seam)
    ontology    -> states + transition grammar (the load-bearing spec)
    semantics   -> grammar-constrained decode + event derivation
    rig         -> multi-cam capture + triangulated ground truth
    annotation  -> model-assisted timeline labeling tool
    eval        -> tier/bucket-layered metrics + regression CI
    api         -> the semantic event stream (the product API)
    views       -> relational state diagram, dashboards, lite overlay
"""

__version__ = "0.0.1"
