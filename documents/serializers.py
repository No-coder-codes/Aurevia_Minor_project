from rest_framework import serializers
from .models import Document
from core.serializers import UserSerializer

class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by_details = UserSerializer(source='uploaded_by', read_only=True)

    class Meta:
        model = Document
        fields = [
            'id', 'project', 'task', 'uploaded_by', 'uploaded_by_details', 
            'file', 'title', 'description', 'uploaded_at'
        ]
        read_only_fields = ['id', 'uploaded_at']
