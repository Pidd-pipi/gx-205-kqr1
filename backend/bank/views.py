from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from bank.models import PaperSnapshot
from bank.serializers import GeneratePaperSerializer, SubmitExamSerializer
from bank.services import generate_paper, pool_summary, serialize_snapshot


QUESTIONS = [
    {
        "id": 101,
        "type": "数字推理",
        "difficulty": "中级",
        "stem": "2，6，12，20，30，下一项是多少？",
        "options": ["38", "40", "42", "44"],
        "answer": "42",
        "explanation": "相邻差为 4、6、8、10，下一差为 12，因此答案为 42。",
        "knowledge": "二级等差",
    },
    {
        "id": 102,
        "type": "逻辑判断",
        "difficulty": "中级",
        "stem": "所有通过高阶训练的人都完成错题复盘，小林完成高阶训练，可推出什么？",
        "options": ["小林完成错题复盘", "小林没有错题", "小林排名第一", "无法判断"],
        "answer": "小林完成错题复盘",
        "explanation": "这是充分条件推理：完成高阶训练可以推出完成错题复盘。",
        "knowledge": "充分条件",
    },
    {
        "id": 103,
        "type": "类比推理",
        "difficulty": "初级",
        "stem": "医生：诊断，相当于教师：？",
        "options": ["备课", "授课", "批改", "讲解"],
        "answer": "授课",
        "explanation": "职业与核心工作行为对应，医生核心行为是诊断，教师核心行为是授课。",
        "knowledge": "职业关系",
    },
]


def build_dashboard() -> dict:
    return {
        "profile": {
            "nickname": "推理训练示例用户",
            "tier": "铂金",
            "totalAnswered": 1260,
            "correctRate": 86.5,
            "streakDays": 19,
            "practiceMinutes": 2480,
        },
        "categories": [
            {"id": 1, "name": "数字推理", "accuracy": 88, "total": 320},
            {"id": 2, "name": "图形推理", "accuracy": 76, "total": 240},
            {"id": 3, "name": "逻辑判断", "accuracy": 91, "total": 280},
            {"id": 4, "name": "类比推理", "accuracy": 84, "total": 210},
            {"id": 5, "name": "演绎推理", "accuracy": 80, "total": 210},
        ],
        "paper": QUESTIONS,
        "wrongBook": [
            {"id": 1, "title": "集合包含关系反推", "type": "演绎推理", "mistakes": 5, "lastPracticed": "05-28"},
            {"id": 2, "title": "九宫格旋转规律", "type": "图形推理", "mistakes": 4, "lastPracticed": "05-27"},
            {"id": 3, "title": "多条件排序", "type": "逻辑判断", "mistakes": 3, "lastPracticed": "05-26"},
        ],
        "rankings": [
            {"rank": 1, "name": "ReasonMax", "tier": "王者", "score": 9820, "accuracy": 94.2},
            {"rank": 2, "name": "DeducePro", "tier": "钻石", "score": 8760, "accuracy": 91.7},
            {"rank": 3, "name": "推理训练示例用户", "tier": "铂金", "score": 7650, "accuracy": 86.5},
        ],
        "radar": [
            {"axis": "数字", "value": 88},
            {"axis": "图形", "value": 76},
            {"axis": "逻辑", "value": 91},
            {"axis": "类比", "value": 84},
            {"axis": "演绎", "value": 80},
        ],
    }


@api_view(["GET"])
def health(_request):
    return Response({"status": "ok", "service": "gxlogic-bank-backend"})


@api_view(["GET"])
def dashboard(_request):
    return Response(build_dashboard())


@api_view(["POST"])
def generate_paper_view(request):
    """生成新试卷：去重抽题、题型均衡、相邻难度补入，并留下带编号快照。"""
    serializer = GeneratePaperSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    paper = generate_paper(
        difficulty=serializer.validated_data["difficulty"],
        amount=int(serializer.validated_data["amount"]),
    )
    return Response({"paper": paper})


@api_view(["GET"])
def paper_detail(request, paper_no: int):
    """按编号回查旧试卷：返回的题目、顺序、难度标记与生成时完全一致。"""
    snapshot = PaperSnapshot.objects.filter(paper_no=paper_no).first()
    if snapshot is None:
        return Response({"detail": f"未找到编号为 JP-{paper_no:04d} 的试卷。"}, status=404)
    return Response({"paper": serialize_snapshot(snapshot)})


@api_view(["GET"])
def paper_history(_request):
    """已生成试卷的历史列表，便于按编号回查。"""
    snapshots = PaperSnapshot.objects.order_by("-paper_no")[:50]
    papers = [
        {
            "paperNo": snapshot.paper_no,
            "paperCode": f"JP-{snapshot.paper_no:04d}",
            "difficulty": snapshot.requested_difficulty,
            "requestedAmount": snapshot.requested_amount,
            "actualAmount": snapshot.actual_amount,
            "replacementCount": snapshot.replacement_count,
            "replacementNote": snapshot.replacement_note,
            "shortage": snapshot.actual_amount < snapshot.requested_amount,
            "shortageCount": snapshot.requested_amount - snapshot.actual_amount,
            "typeGaps": snapshot.type_gaps,
            "createdAt": snapshot.created_at.isoformat() if snapshot.created_at else None,
        }
        for snapshot in snapshots
    ]
    return Response({"papers": papers, "pool": pool_summary()})


@api_view(["POST"])
def submit_exam(request):
    serializer = SubmitExamSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    answers = serializer.validated_data.get("answers", {})
    paper_no = serializer.validated_data.get("paper_no")

    if paper_no is not None:
        snapshot = PaperSnapshot.objects.filter(paper_no=paper_no).first()
        if snapshot is None:
            return Response({"detail": f"未找到编号为 JP-{paper_no:04d} 的试卷。"}, status=404)
        questions = snapshot.questions
        paper_label = f"JP-{snapshot.paper_no:04d}"
    else:
        questions = QUESTIONS
        paper_label = "示例试卷"

    correct = sum(1 for question in questions if answers.get(str(question["id"])) == question["answer"])
    total = len(questions)
    score = round(correct / total * 100) if total else 0
    return Response(
        {
            "score": score,
            "paperCode": paper_label,
            "correctCount": correct,
            "totalCount": total,
            "rank_hint": "本次表现接近黄金 I，继续强化图形推理可冲击铂金。",
            "analysis": ["数字推理稳定", "图形旋转规律仍需复盘", "演绎推理建议练习充分必要条件"],
        }
    )


@api_view(["POST"])
def demo_login(_request):
    User = get_user_model()
    user, _ = User.objects.get_or_create(username="demo", defaults={"email": "demo@example.com"})
    user.set_password("demo1234")
    user.save(update_fields=["password"])
    refresh = RefreshToken.for_user(user)
    return Response({"access": str(refresh.access_token), "refresh": str(refresh)})
