from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from rest_framework.pagination import CursorPagination

User = get_user_model()


def get_user_conversations(user):
    return Conversation.objects.filter(
        participant_1=user
    ) | Conversation.objects.filter(
        participant_2=user
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def conversations(request):
    if request.method == "GET":
        user_conversations = (
            get_user_conversations(request.user)
            .select_related("participant_1", "participant_2")
            .order_by("-created_at")
        )

        serializer = ConversationSerializer(
            user_conversations,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_conversation(request):
    participant_id = request.data.get("participant_id")

    if not participant_id:
        return Response(
            {"error": "participant_id is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if str(participant_id) == str(request.user.id):
        return Response(
            {"error": "You cannot create a conversation with yourself."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    other_user = get_object_or_404(User, id=participant_id)

    conversation = get_user_conversations(request.user).filter(
        participant_1=other_user
    ).first()

    if not conversation:
        conversation = get_user_conversations(request.user).filter(
            participant_2=other_user
        ).first()

    if conversation:
        return Response(
            ConversationSerializer(conversation).data,
            status=status.HTTP_200_OK,
        )

    conversation = Conversation.objects.create(
        participant_1=request.user,
        participant_2=other_user,
    )

    return Response(
        ConversationSerializer(conversation).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def conversation_messages(request, conversation_id):

    # Verify that the logged-in user belongs to this conversation
    conversation = get_object_or_404(
        get_user_conversations(request.user),
        id=conversation_id,
    )

    # Fetch conversation messages
    messages = conversation.messages.select_related("sender").all()

    # Apply cursor pagination
    paginator = MessagePagination()
    paginated_messages = paginator.paginate_queryset(
        messages,
        request,
    )

    # Serialize paginated messages
    serializer = MessageSerializer(
        paginated_messages,
        many=True,
    )

    return paginator.get_paginated_response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_message(request, conversation_id):
    conversation = get_object_or_404(
        get_user_conversations(request.user),
        id=conversation_id,
    )

    serializer = MessageSerializer(data=request.data)

    if serializer.is_valid():
        message = serializer.save(
            sender=request.user,
            conversation=conversation,
        )

        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED,
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST,
    )

class MessagePagination(CursorPagination):
    page_size = 20
    ordering = "-id"