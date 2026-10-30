from rest_framework import serializers
from .models import Task, SubTask, TaskComment, TimeLog
from core.serializers import UserSerializer

class SubTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTask
        fields = ['id', 'task', 'title', 'is_completed', 'created_at']
        read_only_fields = ['id', 'created_at']

class TaskCommentSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)

    class Meta:
        model = TaskComment
        fields = ['id', 'task', 'user', 'user_details', 'content', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

class TimeLogSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)

    class Meta:
        model = TimeLog
        fields = ['id', 'task', 'user', 'user_details', 'start_time', 'end_time', 'duration']
        read_only_fields = ['id', 'user', 'duration']

class TaskSerializer(serializers.ModelSerializer):
    assignee_details = UserSerializer(source='assignee', read_only=True)
    subtasks = SubTaskSerializer(many=True, read_only=True)
    comments = TaskCommentSerializer(many=True, read_only=True)
    time_logs = TimeLogSerializer(many=True, read_only=True)
    dependencies_details = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'project', 'title', 'description', 'assignee', 
            'assignee_details', 'status', 'priority', 'due_date', 
            'dependencies', 'dependencies_details',
            'subtasks', 'comments', 'time_logs',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_dependencies_details(self, obj):
        return [{'id': dep.id, 'title': dep.title, 'status': dep.status} for dep in obj.dependencies.all()]
