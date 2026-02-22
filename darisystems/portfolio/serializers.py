from rest_framework import serializers
from .models import Project

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "title", "slug", "summary", "content", "is_featured", "published_at"]


class ProjectReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "id", "title", "slug", "summary", "content",
            "problem_statement", "solution_overview", "impact",
            "client_name", "industry",
            "is_confidential", "is_featured",
            "status", "published_at",
            "created_at", "updated_at",
        ]

class ProjectWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "title", "slug", "summary", "content",
            "problem_statement", "solution_overview", "impact",
            "client_name", "industry",
            "is_confidential", "is_featured",
            "status", "published_at",
        ]
