"""The per-frame fight graph.

Nodes (A/B + keypoints), edges (contact / relative-position / pressure), global
attrs (regime, who's-on-top prob, against-cage), with per-element confidence and
occluded-in-all-views flags. The key seam between perception and semantics.
See DESIGN.md §2.3.
"""
