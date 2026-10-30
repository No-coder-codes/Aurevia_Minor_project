from rest_framework import serializers
from .models import Message
from core.serializers import UserSerializer

class MessageSerializer(serializers.ModelSerializer):
    sender_details = UserSerializer(source='sender', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'project', 'sender', 'sender_details', 'content', 'timestamp']
        read_only_fields = ['id', 'timestamp']
