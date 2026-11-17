"""V7.2 LangGraph-controlled human-in-the-loop workflow decisions.

The graph NEVER invokes paid models or auto-approves an engineer/QA stage.
A signed human decision determines whether a new explicit Agent attempt can
be proposed. Existing V6.9 HMAC hierarchy remains the source of truth.
"""
from __future__ import annotations
from typing import TypedDict


class ReviewState(TypedDict, total=False):
    step: str
    task_id: str
    qa_decision: str
    approver_decision: str
    reviewer_note: str
    returns: int
    next_action: str
    human_review_required: bool


def review_transition(state: ReviewState) -> ReviewState:
    """Deterministic gate; job completion alone never means task approval."""
    decision = state.get("qa_decision") or "pending"
    approval = state.get("approver_decision") or "pending"
    returns = max(0, int(state.get("returns") or 0))
    if decision == "reject" or approval == "reject":
        if len(str(state.get("reviewer_note") or "").strip()) < 5:
            raise ValueError("Trả lại cần lý do có căn cứ")
        return {**state, "step":"returned", "returns":returns+1,
                "next_action":"engineer_revision_requires_new_job",
                "human_review_required":True}
    if decision == "approve" and approval == "approve":
        return {**state, "step":"ready_for_authorized_final_signoff",
                "next_action":"verify_existing_signed_approval",
                "human_review_required":True}
    if decision == "approve":
        return {**state, "step":"await_manager",
                "next_action":"human_manager_review",
                "human_review_required":True}
    return {**state, "step":"await_qa",
            "next_action":"human_qa_review", "human_review_required":True}


def build_langgraph():
    """Optional installed LangGraph implementation, with a single safe gate."""
    from langgraph.graph import StateGraph, START, END
    graph = StateGraph(ReviewState)
    graph.add_node("human_quality_gate", review_transition)
    graph.add_edge(START,"human_quality_gate")
    graph.add_edge("human_quality_gate",END)
    return graph.compile()


def next_review(state: ReviewState, *, use_langgraph=False) -> ReviewState:
    if use_langgraph:
        return build_langgraph().invoke(state)
    return review_transition(state)
