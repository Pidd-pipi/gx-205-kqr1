from rest_framework import serializers


class GeneratePaperSerializer(serializers.Serializer):
    difficulty = serializers.ChoiceField(choices=["入门", "初级", "中级", "高级", "专家"])
    amount = serializers.ChoiceField(choices=[10, 20, 30, 50])


class SubmitExamSerializer(serializers.Serializer):
    answers = serializers.DictField(child=serializers.CharField(), required=False)
    paper_no = serializers.IntegerField(min_value=1, required=False)
