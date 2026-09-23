"""组卷规则验证脚本（不依赖 PostgreSQL，使用内存 SQLite）。

运行：python3 scripts/verify_paper_rules.py
覆盖：
1. 题型配额相差不超过 1；
2. 卷内无重题；
3. 目标难度充足时不发生补入；
4. 目标难度不足时从相邻难度补入且替换数量正确；
5. 题池不足时返回实际题量与各类型缺口，不重复填充；
6. 同一编号快照回查，题目、顺序、难度标记完全不变。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings_test_sqlite")

import django  # noqa: E402

django.setup()

from django.test.utils import setup_test_environment, teardown_test_environment  # noqa: E402

from django.core.management import call_command  # noqa: E402

setup_test_environment()
call_command("migrate", run_syncdb=True, verbosity=0)

from bank.models import PaperSnapshot  # noqa: E402
from bank.question_pool import QUESTION_POOL, QUESTION_TYPES  # noqa: E402
from bank.services import generate_paper, serialize_snapshot  # noqa: E402

failures = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" -> {detail}" if detail else ""))
    if not condition:
        failures.append(name)


def balanced(counts: dict) -> bool:
    values = list(counts.values())
    return max(values) - min(values) <= 1


def pool_counts(difficulty: str | None = None) -> dict:
    counts = {qtype: 0 for qtype in QUESTION_TYPES}
    for q in QUESTION_POOL:
        if difficulty is None or q["difficulty"] == difficulty:
            counts[q["type"]] += 1
    return counts


# --- 用例 1：入门 10 题，目标难度充足（每题型入门各 2 题），不应补入 ---
paper = generate_paper("入门", 10)
counts = {qtype: 0 for qtype in QUESTION_TYPES}
ids = []
for q in paper["questions"]:
    counts[q["type"]] += 1
    ids.append(q["id"])
check("入门10题·实际题量=10", paper["actualAmount"] == 10, str(paper["actualAmount"]))
check("入门10题·卷内无重题", len(ids) == len(set(ids)), f"ids={len(ids)} unique={len(set(ids))}")
check("入门10题·五题型各2题", counts == {t: 2 for t in QUESTION_TYPES}, str(counts))
check("入门10题·无相邻难度补入", paper["replacementCount"] == 0, str(paper["replacementCount"]))
check("入门10题·无缺口", paper["typeGaps"] == {}, str(paper["typeGaps"]))
check("入门10题·编号为 JP-0001", paper["paperCode"] == "JP-0001", paper["paperCode"])
check("入门10题·每题保留难度标记", all(q["difficulty"] == "入门" for q in paper["questions"]))

# --- 用例 2：专家 10 题，专家题池每题型不足 2，必须相邻补入 ---
paper = generate_paper("专家", 10)
counts = {qtype: 0 for qtype in QUESTION_TYPES}
ids = [q["id"] for q in paper["questions"]]
diff_counts: dict = {}
for q in paper["questions"]:
    counts[q["type"]] += 1
    diff_counts[q["difficulty"]] = diff_counts.get(q["difficulty"], 0) + 1
check("专家10题·题量凑满", paper["actualAmount"] == 10, str(paper["actualAmount"]))
check("专家10题·题型均衡", balanced(counts), str(counts))
check("专家10题·无重题", len(ids) == len(set(ids)))
expert_pool = pool_counts("专家")
expected_replacements = sum(max(0, 2 - expert_pool[t]) for t in QUESTION_TYPES)
check(
    "专家10题·替换数量=各题型专家缺口之和",
    paper["replacementCount"] == expected_replacements,
    f"{paper['replacementCount']} == {expected_replacements}",
)
check("专家10题·替换说明写明数量", f"{expected_replacements} 题" in paper["replacementNote"], paper["replacementNote"])
check("专家10题·每题 replaced 标记与难度一致",
      all((q["difficulty"] != "专家") == q["replaced"] for q in paper["questions"]))
check("专家10题·补入题均来自相邻难度（高级）",
      all(q["difficulty"] in ("专家", "高级") for q in paper["questions"]), str(diff_counts))

# --- 用例 3：入门 50 题，题池总量 48 且图形仅 9、演绎仅 8 ---
# 按轮分配在“数量相差≤1”前提下最多取 44 题（9/8/9/9/8），剩余为真实缺口。
paper = generate_paper("入门", 50)
ids = [q["id"] for q in paper["questions"]]
check("入门50题·实际题量=44（不重复填充）", paper["actualAmount"] == 44, str(paper["actualAmount"]))
check("入门50题·卷内无重题", len(ids) == 44 == len(set(ids)), f"{len(ids)} 题 {len(set(ids))} 唯一")
actual_counts = {t: paper["typeActual"][t] for t in QUESTION_TYPES}
check("入门50题·实际题型数量相差不超过1",
      max(actual_counts.values()) - min(actual_counts.values()) <= 1, str(actual_counts))
check("入门50题·shortage 标记", paper["shortage"] and paper["shortageCount"] == 6,
      f"shortageCount={paper['shortageCount']}")
check("入门50题·缺口按题型合计=6", sum(paper["typeGaps"].values()) == 6, str(paper["typeGaps"]))
# 理想配额各 10；演绎池 8 差 2（均衡下限为 8），其余题型停在 9 各差 1
expected_gaps = {"数字推理": 1, "图形推理": 1, "逻辑判断": 1, "类比推理": 1, "演绎推理": 2}
check("入门50题·各类型缺口明细正确", paper["typeGaps"] == expected_gaps, str(paper["typeGaps"]))
check("入门50题·替换说明含补入数量", "补入" in paper["replacementNote"])

# --- 用例 4：编号连续 ---
numbers = list(PaperSnapshot.objects.order_by("paper_no").values_list("paper_no", flat=True))
check("编号连续递增", numbers == [1, 2, 3], str(numbers))

# --- 用例 5：同一编号回查，题目/顺序/难度标记不变 ---
snapshot = PaperSnapshot.objects.get(paper_no=2)
first_serialized = serialize_snapshot(snapshot)
snapshot.refresh_from_db()
second_serialized = serialize_snapshot(PaperSnapshot.objects.get(paper_no=2))
check("同编号回查·题目ID顺序一致",
      [q["id"] for q in first_serialized["questions"]] == [q["id"] for q in second_serialized["questions"]])
check("同编号回查·难度标记一致",
      [q["difficulty"] for q in first_serialized["questions"]] == [q["difficulty"] for q in second_serialized["questions"]])
check("同编号回查·替换明细一致",
      first_serialized["replacements"] == second_serialized["replacements"])
check("同编号回查·整体JSON一致", first_serialized == second_serialized)

# --- 用例 6：中级 20 题（每题型 4 题），中级池 3/2/2/2/2，全部可补入凑满 ---
paper = generate_paper("中级", 20)
ids = [q["id"] for q in paper["questions"]]
counts = {t: 0 for t in QUESTION_TYPES}
for q in paper["questions"]:
    counts[q["type"]] += 1
check("中级20题·题量凑满20", paper["actualAmount"] == 20)
check("中级20题·题型均衡各4题", counts == {t: 4 for t in QUESTION_TYPES}, str(counts))
check("中级20题·无重题", len(ids) == len(set(ids)))
# 中级题池总数 11，需要补入 9 题
check("中级20题·补入9题", paper["replacementCount"] == 9, str(paper["replacementCount"]))
check("中级20题·补入仅来自初级/高级（相邻距离1）",
      all(q["difficulty"] in ("中级", "初级", "高级") for q in paper["questions"]))
check("中级20题·无缺口", paper["typeGaps"] == {})

# --- 用例 7：高级 50 题，同样受“相差不超过 1”约束取 44 题，缺口 6 ---
paper = generate_paper("高级", 50)
check("高级50题·实际题量=44", paper["actualAmount"] == 44, str(paper["actualAmount"]))
check("高级50题·总缺口=6", sum(paper["typeGaps"].values()) == 6, str(paper["typeGaps"]))
check("高级50题·无重题", len({q["id"] for q in paper["questions"]}) == 44)
check("高级50题·题型数量相差不超过1",
      max(paper["typeActual"].values()) - min(paper["typeActual"].values()) <= 1,
      str(paper["typeActual"]))

print()
if failures:
    print(f"共 {len(failures)} 项失败：{failures}")
    teardown_test_environment()
    sys.exit(1)
print("全部规则验证通过。")
teardown_test_environment()
