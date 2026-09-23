from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from bank.models import PaperSnapshot
from bank.serializers import GeneratePaperSerializer, SubmitExamSerializer
from bank.services import assemble_paper, count_by_type


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


def serialize_snapshot(snapshot: PaperSnapshot) -> dict:
    return {
        "number": snapshot.id,
        "difficulty": snapshot.difficulty,
        "requestedAmount": snapshot.requested_amount,
        "actualAmount": snapshot.actual_amount,
        "typeCounts": count_by_type(snapshot.questions),
        "replacements": snapshot.replacements,
        "gaps": snapshot.gaps,
        "questions": snapshot.questions,
        "createdAt": snapshot.created_at.isoformat() if snapshot.created_at else None,
    }


@api_view(["GET"])
def health(_request):
    return Response({"status": "ok", "service": "gxlogic-bank-backend"})


@api_view(["GET"])
def dashboard(_request):
    return Response(build_dashboard())


@api_view(["POST"])
def generate_paper(request):
    serializer = GeneratePaperSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    difficulty = serializer.validated_data["difficulty"]
    amount = int(serializer.validated_data["amount"])

    plan = assemble_paper(difficulty, amount)
    snapshot = PaperSnapshot.objects.create(
        difficulty=difficulty,
        requested_amount=plan["requestedAmount"],
        actual_amount=plan["actualAmount"],
        questions=plan["questions"],
        replacements=plan["replacements"],
        gaps=plan["gaps"],
    )
    return Response(serialize_snapshot(snapshot))


@api_view(["GET"])
def paper_detail(_request, number):
    snapshot = get_object_or_404(PaperSnapshot, pk=number)
    return Response(serialize_snapshot(snapshot))


@api_view(["POST"])
def submit_exam(request):
    serializer = SubmitExamSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    snapshot = get_object_or_404(PaperSnapshot, pk=serializer.validated_data["paper_number"])
    answers = serializer.validated_data.get("answers", {})

    questions = snapshot.questions
    correct = sum(1 for q in questions if answers.get(str(q["id"])) == q["answer"])
    total = len(questions)
    score = round(correct / total * 100) if total else 0

    type_stats = {}
    for question in questions:
        hit, seen = type_stats.get(question["type"], (0, 0))
        type_stats[question["type"]] = (
            hit + (1 if answers.get(str(question["id"])) == question["answer"] else 0),
            seen + 1,
        )
    analysis = [f"{name} {hit}/{seen} 正确" for name, (hit, seen) in type_stats.items()]

    if score >= 90:
        rank_hint = "本次表现达到钻石水准，继续保持。"
    elif score >= 75:
        rank_hint = "本次表现接近铂金，错题复盘后可冲击钻石。"
    elif score >= 60:
        rank_hint = "本次表现约为黄金，建议针对薄弱题型加练。"
    else:
        rank_hint = "本次表现待提升，建议从入门难度重新巩固。"

    return Response(
        {
            "paper_number": snapshot.id,
            "score": score,
            "correct": correct,
            "total": total,
            "rank_hint": rank_hint,
            "analysis": analysis,
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
