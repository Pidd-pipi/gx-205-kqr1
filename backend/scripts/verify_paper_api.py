"""组卷 API 端到端验证（SQLite 内存库，使用 Django 测试客户端）。"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings_test_sqlite")

import django  # noqa: E402

django.setup()

from django.core.management import call_command  # noqa: E402
from django.test.utils import setup_test_environment, teardown_test_environment  # noqa: E402
from rest_framework.test import APIClient  # noqa: E402

call_command("migrate", run_syncdb=True, verbosity=0)
setup_test_environment()

client = APIClient()
failures = []


def check(name, condition, detail=""):
    print(f"[{'PASS' if condition else 'FAIL'}] {name}" + (f" -> {detail}" if detail else ""))
    if not condition:
        failures.append(name)


# 1. 生成
resp = client.post("/papers/generate/", {"difficulty": "专家", "amount": 10}, format="json")
check("生成接口 200", resp.status_code == 200, str(resp.status_code))
paper = resp.data["paper"]
check("返回编号", paper["paperCode"] == "JP-0001")
check("返回替换说明", "补入" in paper["replacementNote"])
check("题目带难度标记", all("difficulty" in q for q in paper["questions"]))

# 2. 同编号回查内容一致
resp2 = client.get(f"/papers/{paper['paperNo']}/")
check("回查接口 200", resp2.status_code == 200)
paper2 = resp2.data["paper"]
check("回查题目ID顺序一致",
      [q["id"] for q in paper["questions"]] == [q["id"] for q in paper2["questions"]])
check("回查难度标记一致",
      [q["difficulty"] for q in paper["questions"]] == [q["difficulty"] for q in paper2["questions"]])

# 3. 编号不存在
resp3 = client.get("/papers/999/")
check("不存在编号返回 404", resp3.status_code == 404)

# 4. 题池不足场景
resp4 = client.post("/papers/generate/", {"difficulty": "入门", "amount": 50}, format="json")
short_paper = resp4.data["paper"]
check("题池不足返回实际题量", short_paper["actualAmount"] == 44, str(short_paper["actualAmount"]))
check("返回各类型缺口", sum(short_paper["typeGaps"].values()) == 6, str(short_paper["typeGaps"]))

# 5. 历史列表
resp5 = client.get("/papers/history/")
check("历史列表 200", resp5.status_code == 200)
check("历史列表含2份试卷", len(resp5.data["papers"]) == 2, str(len(resp5.data["papers"])))
check("历史列表按编号倒序",
      [p["paperNo"] for p in resp5.data["papers"]] == [2, 1])
check("历史列表含题池存量", resp5.data["pool"]["数字推理"]["入门"] == 2)

# 6. 参数校验
resp6 = client.post("/papers/generate/", {"difficulty": "地狱", "amount": 10}, format="json")
check("非法难度 400", resp6.status_code == 400)
resp7 = client.post("/papers/generate/", {"difficulty": "中级", "amount": 13}, format="json")
check("非法题量 400", resp7.status_code == 400)

# 7. 按快照试卷计分
answers = {str(q["id"]): q["answer"] for q in paper2["questions"]}
resp8 = client.post("/exams/submit/", {"paper_no": 1, "answers": answers}, format="json")
check("全对得 100 分", resp8.data["score"] == 100, str(resp8.data))
check("计分返回试卷编号", resp8.data["paperCode"] == "JP-0001")

print()
if failures:
    print(f"共 {len(failures)} 项失败：{failures}")
    teardown_test_environment()
    sys.exit(1)
print("API 端到端验证通过。")
teardown_test_environment()
