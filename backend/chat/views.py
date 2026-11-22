from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Conversation, Message, MessageReaction, PinnedMessage, MessageAttachment, ConversationParticipant
from .serializers import ConversationSerializer, MessageSerializer, MessageReactionSerializer, PinnedMessageSerializer, MessageAttachmentSerializer
from rest_framework.pagination import CursorPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import (
    api_view,
    permission_classes,
    parser_classes,
)

User = get_user_model()


def get_user_conversations(user):
    direct_conversations = Conversation.objects.filter(
        participant_1=user,
        is_group=False,
    ) | Conversation.objects.filter(
        participant_2=user,
        is_group=False,
    )

    group_conversations = Conversation.objects.filter(
        participants__user=user,
        is_group=True,
    )

    return (direct_conversations | group_conversations).distinct()


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
                            participant_1=other_user,
                            participant_2=request.user,
                            is_group=False,
                        ).first()

    if not conversation:
        conversation = get_user_conversations(request.user).filter(
            participant_1=request.user,
            participant_2=other_user,
            is_group=False,
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

# =============================
# Create Group Coversation
# =============================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_group_conversation(request):

    name = request.data.get("name")
    participant_ids = request.data.get("participant_ids")

    if not name or not name.strip():
        return Response(
            {"error": "Group name is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not isinstance(participant_ids, list) or not participant_ids:
        return Response(
            {"error": "participant_ids must be a non-empty list."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(participant_ids) != len(set(map(str, participant_ids))):
        return Response(
            {"error": "Duplicate participants are not allowed."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if str(request.user.id) in map(str, participant_ids):
        return Response(
            {"error": "You are automatically included in the group."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(name.strip()) > 100:
        return Response(
            {"error": "Group name cannot exceed 100 characters."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    users = list(User.objects.filter(id__in=participant_ids))

    if len(users) != len(participant_ids):
        return Response(
            {"error": "One or more users do not exist."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    conversation = Conversation.objects.create(
        name=name.strip(),
        is_group=True,
        participant_1=request.user,
        participant_2=request.user,
    )

    members = [request.user] + users

    ConversationParticipant.objects.bulk_create([
        ConversationParticipant(
            conversation=conversation,
            user=user,
        )
        for user in members
    ])

    return Response(
        ConversationSerializer(conversation).data,
        status=status.HTTP_201_CREATED,
    )

# ==================================
# create_conversation
# ==================================

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

    # Broadcast the forwarded message through WebSocket
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"chat_{destination_conversation.id}",
        {
            "type": "chat_message",
            "message_id": forwarded_message.id,
            "message": forwarded_message.content,
            "sender": request.user.username,
            "sender_id": request.user.id,
            "timestamp": forwarded_message.timestamp.isoformat(),
            "reply_to": None,
            "reply_to_details": None,
            "is_forwarded": True,
            "forwarded_from": original_message.id,
            "forwarded_from_username": original_message.sender.username,
        },
    )

    serializer = MessageSerializer(forwarded_message)

    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED,
    )


# ===========================
# Pin Message
# ===========================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def pin_message(request, conversation_id, message_id):

    # Step 1: Verify conversation membership
    conversation = get_object_or_404(
        get_user_conversations(request.user),
        id=conversation_id,
    )

    # Step 2: Verify message belongs to the conversation
    message = get_object_or_404(
        Message,
        id=message_id,
        conversation=conversation,
    )

    # Step 3: Create pinned message or retrieve existing record
    pinned_message, created = PinnedMessage.objects.get_or_create(
        conversation=conversation,
        message=message,
        defaults={
            "pinned_by": request.user,
        },
    )

    # Step 4: Broadcast pin event only when newly pinned
    if created:
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"chat_{conversation.id}",
            {
                "type": "message_pinned",
                "message_id": message.id,
                "pinned_by": request.user.id,
                "pinned_by_username": request.user.username,
                "pinned_at": pinned_message.pinned_at.isoformat(),
            },
        )

    # Step 5: Return response
    serializer = PinnedMessageSerializer(pinned_message)

    return Response(
        serializer.data,
        status=(
            status.HTTP_201_CREATED
            if created
            else status.HTTP_200_OK
        ),
    )

# ===========================
# Unpin Message
# ===========================

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def unpin_message(request, conversation_id, message_id):

    # Verify conversation membership
    conversation = get_object_or_404(
        get_user_conversations(request.user),
        id=conversation_id,
    )

    # Verify message belongs to the conversation
    message = get_object_or_404(
        Message,
        id=message_id,
        conversation=conversation,
    )

    # Find the pinned message
    pinned_message = get_object_or_404(
        PinnedMessage,
        conversation=conversation,
        message=message,
    )

    # Delete the pinned record
    pinned_message.delete()

    # Broadcast unpin event through WebSocket
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"chat_{conversation.id}",
        {
            "type": "message_unpinned",
            "message_id": message.id,
            "unpinned_by": request.user.id,
            "unpinned_by_username": request.user.username,
        },
    )

    return Response(
        {"message": "Message unpinned successfully."},
        status=status.HTTP_200_OK,
    )

# ===========================
# Get Pinned Messages
# ===========================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_pinned_messages(request, conversation_id):

    # Verify conversation membership
    conversation = get_object_or_404(
        get_user_conversations(request.user),
        id=conversation_id,
    )

    # Fetch pinned messages
    pinned_messages = (
        PinnedMessage.objects
        .filter(conversation=conversation)
        .select_related(
            "message",
            "message__sender",
            "pinned_by",
        )
        .order_by("-pinned_at")
    )

    serializer = PinnedMessageSerializer(
        pinned_messages,
        many=True,
    )

    return Response(
        serializer.data,
        status=status.HTTP_200_OK,
    )

# ===========================
# Message Search
# ===========================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_messages(request):
    query = request.query_params.get("q", "").strip()

    # Validate search query
    if not query:
        return Response(
            {"error": "Search query is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Get conversations belonging to the authenticated user
    user_conversations = get_user_conversations(request.user)

    # Search messages only within user's conversations
    messages = (
        Message.objects
        .filter(
            conversation__in=user_conversations,
            content__icontains=query,
        )
        .select_related(
            "sender",
            "conversation",
        )
        .order_by("-id")
    )

    # Apply pagination
    paginator = MessagePagination()
    paginated_messages = paginator.paginate_queryset(
        messages,
        request,
    )

    serializer = MessageSerializer(
        paginated_messages,
        many=True,
    )

    return paginator.get_paginated_response(serializer.data)

# =====================================
# Upload attacment API
# =====================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_attachment(request, conversation_id, message_id):
    # 1. Verify conversation membership
    conversation = get_object_or_404(
        get_user_conversations(request.user),
        id=conversation_id,
    )

    # 2. Verify message belongs to this conversation
    message = get_object_or_404(
        Message,
        id=message_id,
        conversation=conversation,
    )

    # 3. Get uploaded file
    uploaded_file = request.FILES.get("file")

    if not uploaded_file:
        return Response(
            {"error": "No file was uploaded."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 4. Validate attachment
    serializer = MessageAttachmentSerializer(
        data={"file": uploaded_file}
    )

    if serializer.is_valid():

        # 5. Save attachment metadata
        attachment = serializer.save(
            message=message,
            file_name=uploaded_file.name,
            file_type=uploaded_file.content_type or "application/octet-stream",
            file_size=uploaded_file.size,
        )

        # 6. Return response
        return Response(
            MessageAttachmentSerializer(attachment).data,
            status=status.HTTP_201_CREATED,
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST,
    )

class MessagePagination(CursorPagination):
    page_size = 20
    ordering = "-id"


