from django.conf import settings
from django.db import models


class LogicQuestion(models.Model):
    QUESTION_TYPES = [
        ("number", "数字推理"),
        ("figure", "图形推理"),
        ("logic", "逻辑判断"),
        ("analogy", "类比推理"),
        ("deduction", "演绎推理"),
    ]

    title = models.CharField(max_length=120)
    question_type = models.CharField(max_length=32, choices=QUESTION_TYPES)
    difficulty = models.CharField(max_length=16)
    stem = models.TextField()
    answer = models.CharField(max_length=32)
    explanation = models.TextField()
    knowledge = models.CharField(max_length=120)
    image = models.ImageField(upload_to="questions/", blank=True)

    def __str__(self) -> str:
        return self.title


class WrongBookEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(LogicQuestion, on_delete=models.CASCADE)
    mistakes = models.PositiveIntegerField(default=1)
    favorited = models.BooleanField(default=False)
    last_practiced_at = models.DateField(auto_now=True)

    class Meta:
        unique_together = ("user", "question")


class PaperSnapshot(models.Model):
    """一次组卷结果的不可变快照。

    同一编号再次打开时，题目、顺序与难度标记均以 questions 快照为准，
    不随题池或随机结果变化。
    """

    paper_no = models.PositiveIntegerField(unique=True, verbose_name="试卷编号")
    requested_difficulty = models.CharField(max_length=16, verbose_name="选定难度")
    requested_amount = models.PositiveIntegerField(verbose_name="选定题量")
    actual_amount = models.PositiveIntegerField(verbose_name="实际题量")
    questions = models.JSONField(verbose_name="题目顺序快照")
    type_quota = models.JSONField(default=dict, verbose_name="各题型目标配额")
    type_actual = models.JSONField(default=dict, verbose_name="各题型实际题量")
    type_gaps = models.JSONField(default=dict, verbose_name="各题型缺口")
    replacements = models.JSONField(default=list, verbose_name="相邻难度补入明细")
    replacement_count = models.PositiveIntegerField(default=0, verbose_name="补入题数")
    replacement_note = models.CharField(max_length=255, blank=True, verbose_name="替换说明")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-paper_no"]

    def __str__(self) -> str:
        return f"试卷 JP-{self.paper_no:04d}"
