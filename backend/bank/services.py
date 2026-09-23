"""智能组卷：按题型均衡抽题；当前难度不足时从相邻难度（±1）补入并记录替换数量；
题池仍不足则如实返回实际题量和各类型缺口，绝不重复填充。"""

import random

from bank.question_bank import DIFFICULTIES, POOL_BY_TYPE_DIFF, QUESTION_TYPES

TYPE_NAMES = [name for _, name in QUESTION_TYPES]


def assemble_paper(difficulty: str, amount: int, rng: random.Random | None = None) -> dict:
    """生成一套试卷的完整方案（不落库），调用方负责持久化快照。"""
    rng = rng or random.Random()

    # 五种题型配额相差不超过 1
    base, extra = divmod(amount, len(TYPE_NAMES))
    quotas = {name: base + (1 if index < extra else 0) for index, name in enumerate(TYPE_NAMES)}

    # 补入来源仅限相邻难度（±1），先低后高
    level = DIFFICULTIES.index(difficulty)
    neighbors = [
        item
        for item in (
            DIFFICULTIES[level - 1] if level > 0 else None,
            DIFFICULTIES[level + 1] if level < len(DIFFICULTIES) - 1 else None,
        )
        if item
    ]
    sources = [difficulty, *neighbors]

    questions, replacements, gaps = [], [], []
    for name in TYPE_NAMES:
        quota = quotas[name]
        picked, used_ids, borrowed = [], set(), {}
        for source in sources:
            if len(picked) >= quota:
                break
            pool = [q for q in POOL_BY_TYPE_DIFF[(name, source)] if q["id"] not in used_ids]
            rng.shuffle(pool)
            take = pool[: quota - len(picked)]
            used_ids.update(q["id"] for q in take)
            picked.extend(take)
            if take and source != difficulty:
                borrowed[source] = borrowed.get(source, 0) + len(take)
        if borrowed:
            replacements.append({"type": name, "count": sum(borrowed.values()), "from": borrowed})
        if len(picked) < quota:
            gaps.append({"type": name, "missing": quota - len(picked)})
        questions.extend(picked)

    rng.shuffle(questions)
    ordered = [
        {**question, "substituted": question["difficulty"] != difficulty}
        for question in questions
    ]
    return {
        "difficulty": difficulty,
        "requestedAmount": amount,
        "actualAmount": len(ordered),
        "typeCounts": count_by_type(ordered),
        "replacements": replacements,
        "gaps": gaps,
        "questions": ordered,
    }


def count_by_type(questions) -> dict:
    counts = {name: 0 for name in TYPE_NAMES}
    for question in questions:
        counts[question["type"]] = counts.get(question["type"], 0) + 1
    return counts
