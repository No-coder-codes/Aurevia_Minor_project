from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Project
from core.serializers import UserSerializer

User = get_user_model()

class ProjectSerializer(serializers.ModelSerializer):
    manager_details = UserSerializer(source='manager', read_only=True)
    member_details = UserSerializer(source='members', many=True, read_only=True)
    progress_percentage = serializers.IntegerField(read_only=True)
    total_tasks = serializers.SerializerMethodField()
    completed_tasks = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'start_date', 'end_date',
            'status', 'manager', 'manager_details', 'members',
            'member_details', 'progress_percentage', 'total_tasks',
            'completed_tasks', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_total_tasks(self, obj):
        return obj.tasks.count()

    def get_completed_tasks(self, obj):
        return obj.tasks.filter(status='done').count()


class ProjectDetailSerializer(ProjectSerializer):
    members_details = UserSerializer(source='members', many=True, read_only=True)

    class Meta(ProjectSerializer.Meta):
        pass
