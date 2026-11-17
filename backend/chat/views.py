from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Conversation, Message, MessageReaction
from .serializers import ConversationSerializer, MessageSerializer, MessageReactionSerializer
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
    messages = (
                        conversation.messages
                        .select_related("sender")
                        .prefetch_related("reactions__user")
                        .all()
                    )
    
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

@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def add_message_reaction(request, conversation_id, message_id):

    # Verify that the logged-in user belongs to this conversation
    conversation = get_object_or_404(
        get_user_conversations(request.user),
        id=conversation_id,
    )

    # Verify that the message belongs to this conversation
    message = get_object_or_404(
        Message,
        id=message_id,
        conversation=conversation,
    )

    # Remove the user's existing reaction
    if request.method == "DELETE":
        reaction = get_object_or_404(
            MessageReaction,
            message=message,
            user=request.user,
        )

        reaction.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    # Get or create the user's reaction
    reaction, created = MessageReaction.objects.update_or_create(
        message=message,
        user=request.user,
        defaults={
            "emoji": request.data.get("emoji", ""),
        },
    )

    serializer = MessageReactionSerializer(reaction)

    return Response(
        serializer.data,
        status=(
            status.HTTP_201_CREATED
            if created
            else status.HTTP_200_OK
        ),
    )

# ===========================
# forward_message
#===========================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def forward_message(request, conversation_id, message_id):

    # Check whether the user belongs to the source conversation
    source_conversation = get_object_or_404(
        get_user_conversations(request.user),
        id=conversation_id,
    )

    # Find the message to forward
    original_message = get_object_or_404(
        Message,
        id=message_id,
        conversation=source_conversation,
    )

    # Get the destination conversation ID
    destination_id = request.data.get("destination_conversation_id")

    if not destination_id:
        return Response(
            {"error": "destination_conversation_id is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check whether the user belongs to the destination conversation
    destination_conversation = get_object_or_404(
        get_user_conversations(request.user),
        id=destination_id,
    )

    # Create a new forwarded message
    forwarded_message = Message.objects.create(
        conversation=destination_conversation,
        sender=request.user,
        content=original_message.content,
        is_forwarded=True,
        forwarded_from=original_message,
    )

    serializer = MessageSerializer(forwarded_message)

    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED,
    )

class MessagePagination(CursorPagination):
    page_size = 20
    ordering = "-id"