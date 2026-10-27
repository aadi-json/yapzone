from rest_framework import serializers
from .models import Message, Conversation


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(
        source="sender.username",
        read_only=True
    )

    class Meta:
        model = Message

        fields = [
            "id",
            "conversation",
            "sender",
            "sender_username",
            "content",
            "timestamp",
        ]

        read_only_fields = [
            "id",
            "conversation",
            "sender",
            "sender_username",
            "timestamp",
        ]

    def validate_content(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Message content cannot be empty."
            )

        return value


#Conversation Serializer
class ConversationSerializer(serializers.ModelSerializer):
    participant_1_username = serializers.CharField(
        source="participant_1.username",
        read_only=True,
    )

    participant_2_username = serializers.CharField(
        source="participant_2.username",
        read_only=True,
    )

    class Meta:
        model = Conversation

        fields = [
            "id",
            "participant_1",
            "participant_1_username",
            "participant_2",
            "participant_2_username",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "participant_1",
            "participant_1_username",
            "participant_2_username",
            "created_at",
        ]