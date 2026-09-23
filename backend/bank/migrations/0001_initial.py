import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="LogicQuestion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=120)),
                (
                    "question_type",
                    models.CharField(
                        choices=[
                            ("number", "数字推理"),
                            ("figure", "图形推理"),
                            ("logic", "逻辑判断"),
                            ("analogy", "类比推理"),
                            ("deduction", "演绎推理"),
                        ],
                        max_length=32,
                    ),
                ),
                ("difficulty", models.CharField(max_length=16)),
                ("stem", models.TextField()),
                ("answer", models.CharField(max_length=32)),
                ("explanation", models.TextField()),
                ("knowledge", models.CharField(max_length=120)),
                ("image", models.ImageField(blank=True, upload_to="questions/")),
            ],
        ),
        migrations.CreateModel(
            name="PaperSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("difficulty", models.CharField(max_length=16)),
                ("requested_amount", models.PositiveIntegerField()),
                ("actual_amount", models.PositiveIntegerField()),
                ("questions", models.JSONField(default=list)),
                ("replacements", models.JSONField(default=list)),
                ("gaps", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-id"],
            },
        ),
        migrations.CreateModel(
            name="WrongBookEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("mistakes", models.PositiveIntegerField(default=1)),
                ("favorited", models.BooleanField(default=False)),
                ("last_practiced_at", models.DateField(auto_now=True)),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="bank.logicquestion")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "unique_together": {("user", "question")},
            },
        ),
    ]
