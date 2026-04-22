from rest_framework import serializers
from chatbot.models import ChatSession


class ChatRequestSerializer(serializers.Serializer):
    message=serializers.CharField(
        max_length=2000,
        trim_whitespace=True,
        required=True
    )
    
    session_id=serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1
    )
    def validate_message(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message cannot be empty.")
        return value

class ChatResponseSerializer(serializers.Serializer):
    reply=serializers.CharField()
    session_id=serializers.IntegerField(min_value=1)
    
class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'created_at']
        