"""Shared persisted fixture helpers for bounded Decision Policy probes."""
from scripts.verify_phase3d3a_decision_policy_postgres import build,evaluate,types,roots
from scripts import verify_phase3d2_decision_evidence_matrix as d2
def cleanup():
 while roots:d2._cleanup([roots.pop()],[])
