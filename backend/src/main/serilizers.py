from rest_framework import serializers
from .models import WeeklyGoal


class WeeklyGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyGoal
        fields = [
            "id",
            "text",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]