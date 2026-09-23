"""智能组卷服务。

规则：
1. 卷内不重题：题池中的每道题在一套卷内最多出现一次，题池不足时只返回实际题量，
   绝不用循环填充凑数。
2. 五种题型数量均衡：按“轮”分配，每一轮每种题型至多取 1 题；某题型题池枯竭后，
   其他题型的题数立即封顶为“枯竭题数 + 1”，因此最终各题型实际数量相差不超过 1。
3. 难度补入：取题时先取目标难度；目标难度不足则从难度轴上距离最近的相邻难度逐层
   补入（距离 1 的两侧难度优先，随后距离 2 …），并记录每道补入题与替换数量。
4. 真实缺口：用尽题池仍凑不满时，按题型记录“理想配额 - 实际数量”的缺口，
   由调用方持久化并返回，不做任何重复填充。
"""

from __future__ import annotations

import random
from collections import defaultdict

from bank.models import PaperSnapshot
from bank.question_pool import DIFFICULTIES, QUESTION_POOL, QUESTION_TYPES


def _build_indexes() -> dict:
    """返回 (题型 -> 难度 -> [题目]) 索引。"""
    by_type_difficulty: dict = {qtype: {d: [] for d in DIFFICULTIES} for qtype in QUESTION_TYPES}
    for question in QUESTION_POOL:
        by_type_difficulty[question["type"]][question["difficulty"]].append(question)
    return by_type_difficulty


def ideal_quota(amount: int) -> dict:
    """题池无限时每轮分配对应的理想配额，各题型相差不超过 1。"""
    base, extra = divmod(amount, len(QUESTION_TYPES))
    return {qtype: base + (1 if index < extra else 0) for index, qtype in enumerate(QUESTION_TYPES)}


def _difficulty_layers(target: str) -> list[tuple[int, list[str]]]:
    """按与目标难度的距离从近到远分层，每层列出该距离的难度（不含目标难度本身）。"""
    center = DIFFICULTIES.index(target)
    layers: list[tuple[int, list[str]]] = []
    for distance in range(1, len(DIFFICULTIES)):
        indexes = [center - distance, center + distance]
        levels = [DIFFICULTIES[i] for i in indexes if 0 <= i < len(DIFFICULTIES)]
        layers.append((distance, levels))
    return layers


def _replace_label(distance: int) -> str:
    if distance == 1:
        return "相邻难度补入"
    return f"跨 {distance} 个难度等级补入"


def _build_replacement_note(replaced_counter: dict, target: str) -> str:
    if not replaced_counter:
        return f"题池“{target}”题目充足，全部为目标难度题目。"
    parts = [f"{level} {count} 题" for level, count in sorted(replaced_counter.items())]
    return (
        f"目标难度“{target}”不足，已从相邻难度补入 {'，'.join(parts)}"
        f"（共 {sum(replaced_counter.values())} 题），题目保留原始难度标记。"
    )


def _freeze_question(question: dict, target_difficulty: str, distance: int) -> dict:
    """序列化单题快照，并标注其相对于目标难度的补入信息。"""
    frozen = {key: value for key, value in question.items()}
    frozen["requested_difficulty"] = target_difficulty
    frozen["replaced"] = distance > 0
    frozen["replace_distance"] = distance
    frozen["replace_label"] = "" if distance == 0 else _replace_label(distance)
    return frozen


def generate_paper(difficulty: str, amount: int) -> dict:
    """生成一套不重题、题型均衡的练习卷并持久化为带编号快照。"""
    by_type_difficulty = _build_indexes()

    rng = random.SystemRandom()
    used_ids: set[int] = set()
    selected: list[dict] = []
    actual: dict = {qtype: 0 for qtype in QUESTION_TYPES}
    replacements: list[dict] = []
    replaced_counter: dict = defaultdict(int)
    exhausted: set[str] = set()

    def take_one(qtype: str) -> dict | None:
        """在某题型中按目标难度→相邻难度顺序取一道未用过的题，返回快照题。"""
        for level_distance, levels in [(0, [difficulty])] + _difficulty_layers(difficulty):
            bucket = [q for level in levels for q in by_type_difficulty[qtype][level]]
            rng.shuffle(bucket)
            for question in bucket:
                if question["id"] in used_ids:
                    continue
                used_ids.add(question["id"])
                frozen = _freeze_question(question, difficulty, level_distance)
                if level_distance > 0:
                    replaced_counter[question["difficulty"]] += 1
                    replacements.append(
                        {
                            "question_id": question["id"],
                            "type": qtype,
                            "target_difficulty": difficulty,
                            "actual_difficulty": question["difficulty"],
                            "distance": level_distance,
                            "label": _replace_label(level_distance),
                        }
                    )
                return frozen
        return None

    # 逐轮分配：每轮每种仍可出题的题型各取 1 题。
    # 一旦有题型在第 k 轮枯竭，其他题型最多只能再多取 1 题（上限 k+1），
    # 从而保证题型数量相差不超过 1，且绝不靠重复题目凑量。
    total_rounds = (amount + len(QUESTION_TYPES) - 1) // len(QUESTION_TYPES)
    cap = total_rounds
    for round_index in range(total_rounds):
        if len(selected) >= amount or round_index >= cap:
            break
        for qtype in QUESTION_TYPES:
            if len(selected) >= amount:
                break
            if qtype in exhausted or actual[qtype] >= cap:
                continue
            frozen = take_one(qtype)
            if frozen is None:
                exhausted.add(qtype)
                # 枯竭发生在第 round_index 轮：该题型停在 round_index 题，其余上限 round_index+1
                cap = min(cap, round_index + 1)
                continue
            actual[qtype] += 1
            selected.append(frozen)

    quota = ideal_quota(amount)
    gaps = {qtype: quota[qtype] - actual[qtype] for qtype in QUESTION_TYPES if actual[qtype] < quota[qtype]}

    # 卷内顺序在快照生成时一次性冻结
    rng.shuffle(selected)

    from django.db import transaction

    with transaction.atomic():
        paper_no = _next_paper_no()
        snapshot = PaperSnapshot.objects.create(
            paper_no=paper_no,
            requested_difficulty=difficulty,
            requested_amount=amount,
            actual_amount=len(selected),
            questions=selected,
            type_quota=quota,
            type_actual=actual,
            type_gaps=gaps,
            replacements=replacements,
            replacement_count=len(replacements),
            replacement_note=_build_replacement_note(replaced_counter, difficulty),
        )
    return serialize_snapshot(snapshot)


def _next_paper_no() -> int:
    """分配下一个连续试卷编号；须在事务内调用，行锁 + 唯一约束共同兜底。"""
    last = PaperSnapshot.objects.select_for_update().order_by("-paper_no").first()
    candidate = (last.paper_no + 1) if last else 1
    while PaperSnapshot.objects.filter(paper_no=candidate).exists():
        candidate += 1
    return candidate


def serialize_snapshot(snapshot: PaperSnapshot) -> dict:
    """快照 -> API 响应结构；同一编号回查时内容与生成时完全一致。"""
    return {
        "paperNo": snapshot.paper_no,
        "paperCode": f"JP-{snapshot.paper_no:04d}",
        "difficulty": snapshot.requested_difficulty,
        "requestedAmount": snapshot.requested_amount,
        "actualAmount": snapshot.actual_amount,
        "questions": snapshot.questions,
        "typeQuota": snapshot.type_quota,
        "typeActual": snapshot.type_actual,
        "typeGaps": snapshot.type_gaps,
        "replacements": snapshot.replacements,
        "replacementCount": snapshot.replacement_count,
        "replacementNote": snapshot.replacement_note,
        "shortage": snapshot.actual_amount < snapshot.requested_amount,
        "shortageCount": snapshot.requested_amount - snapshot.actual_amount,
        "createdAt": snapshot.created_at.isoformat() if snapshot.created_at else None,
    }


def pool_summary() -> dict:
    """题池在 题型 × 难度 上的存量，供前端展示真实题池规模。"""
    by_type_difficulty = _build_indexes()
    return {
        qtype: {level: len(by_type_difficulty[qtype][level]) for level in DIFFICULTIES}
        for qtype in QUESTION_TYPES
    }
