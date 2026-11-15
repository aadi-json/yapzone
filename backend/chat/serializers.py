from rest_framework import serializers
from .models import Message, Conversation
from django.contrib.auth import get_user_model  


class MessageReplySerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(
        source="sender.username",
        read_only=True
    )

    class Meta:
        model = Message
        fields = [
            "id",
            "sender_username",
            "content",
            "timestamp",
        ]


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(
        source="sender.username",
        read_only=True
    )

    reply_to = serializers.PrimaryKeyRelatedField(
        queryset=Message.objects.all(),
        required=False,
        allow_null=True
    )

    reply_to_details = MessageReplySerializer(
        source="reply_to",
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
            "reply_to",
            "reply_to_details",
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

    def validate_reply_to(self, value):
        if value is None:
            return value

        conversation = self.context.get("conversation")

        if value.conversation_id != conversation.id:
            raise serializers.ValidationError(
                "You can only reply to messages in the same conversation."
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


User = get_user_model()

#register user serializer
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)