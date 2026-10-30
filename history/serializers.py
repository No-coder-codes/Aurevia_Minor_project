from rest_framework import serializers
from .models import ActivityLog
from core.serializers import UserSerializer

class ActivityLogSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)

    class Meta:
        model = ActivityLog
        fields = ['id', 'user', 'user_details', 'action', 'target_content_type', 'target_object_id', 'timestamp']
        read_only_fields = ['id', 'timestamp']
