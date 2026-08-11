"""
Student-proposing deferred acceptance (Gale-Shapley) with per-branch cutoffs.

Why this instead of a greedy single pass: a greedy "fill highest-ranked branch
first" allocation can leave a student worse off than a stable matching would,
because it doesn't let an already-held (but weaker) candidate get bumped later
by a stronger candidate who proposes to that branch afterward. Deferred
acceptance is the standard, provably stable algorithm for exactly this
preference + merit + capacity problem (same family used in JEE/JoSAA style
counselling).
"""

from dataclasses import dataclass


@dataclass
class Candidate:
    application_id: int
    student_id: int
    preferences: list[int]  # ordered branch_ids, most preferred first
    rank_key: tuple  # sort key, ascending = better (see build below)
    next_pref_index: int = 0
    held_branch_id: int | None = None


@dataclass
class BranchInfo:
    branch_id: int
    capacity: int
    cutoff_marks: float


def build_rank_key(total, maths, phy, chem, english) -> tuple:
    """Descending priority on marks == ascending on the negated tuple."""
    return (-total, -maths, -phy, -chem, -english)


def run_deferred_acceptance(
    candidates: list[Candidate], branches: dict[int, BranchInfo]
) -> dict[int, int]:
    """
    Returns {application_id: branch_id} for candidates who end up holding a seat.
    Candidates who never meet cutoff anywhere, or run out of preferences before
    getting held, are simply absent from the result (no offer for them this round).
    """
    held: dict[int, list[Candidate]] = {bid: [] for bid in branches}
    free = list(candidates)

    while free:
        proposals: dict[int, list[Candidate]] = {bid: [] for bid in branches}
        still_free: list[Candidate] = []

        for c in free:
            while c.next_pref_index < len(c.preferences):
                bid = c.preferences[c.next_pref_index]
                c.next_pref_index += 1
                branch = branches.get(bid)
                if branch is None:
                    continue  # unknown branch id, skip defensively
                total_marks = -c.rank_key[0]
                if total_marks < branch.cutoff_marks:
                    continue  # doesn't clear cutoff for this branch, try next pref
                proposals[bid].append(c)
                break
            # if the while loop exits with no break, c has exhausted every
            # preference (or failed every cutoff) -> permanently out, don't requeue

        if not any(proposals.values()):
            break  # nobody has any proposal left to make -> stable state reached

        for bid, new_props in proposals.items():
            if not new_props:
                continue
            branch = branches[bid]
            pool = held[bid] + new_props
            pool.sort(key=lambda c: c.rank_key)  # best rank first
            keep, bump = pool[: branch.capacity], pool[branch.capacity :]
            held[bid] = keep
            for c in keep:
                c.held_branch_id = bid
            for c in bump:
                c.held_branch_id = None
                still_free.append(c)  # will retry with their next preference

        free = still_free

    return {c.application_id: bid for bid, cands in held.items() for c in cands}
