from django.db.migrations import serializer
from django.http import request
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework import status
from .models import Conversation, Message
from .serializers import MessageSerializer, ConversationSerializer

# Cnversation Views
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def conversation_messages(request, conversation_id):
    conversation = get_object_or_404(
        Conversation.objects.filter(
            participant_1=request.user
        ) | Conversation.objects.filter(
            participant_2=request.user
        ),
        id=conversation_id,
    )

    messages = conversation.messages.select_related("sender").all()

    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data, status=200)




#create a new message in a conversation
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_message(request, conversation_id):
    conversation  = get_object_or_404(
        Conversation.objects.filter(
            participant_1 = request.user
        ) | Conversation.objects.filter(
            participant_2 = request.user
        ),
            id  = conversation_id
    )

    serializer = MessageSerializer(data=request.data)

    if serializer.is_valid():
        message = serializer.save(
            sender = request.user, 
            conversation = conversation
        )
        return Response(
            MessageSerializer(message).data, 
            status=201
        )
    return Response(serializer.errors, status=400)


#conversation creation view
User = get_user_model()
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

    existing_conversation = Conversation.objects.filter(
        participant_1=request.user,
        participant_2=other_user,
    ).first()

    if not existing_conversation:
        existing_conversation = Conversation.objects.filter(
            participant_1=other_user,
            participant_2=request.user,
        ).first()

    if existing_conversation:
        return Response(
            ConversationSerializer(existing_conversation).data,
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

# List all conversations for the authenticated user
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_conversations(request):
    user_conversations = (
        Conversation.objects.filter(participant_1=request.user)
        | Conversation.objects.filter(participant_2=request.user)
    )

    user_conversations = user_conversations.select_related(
        "participant_1",
        "participant_2",
    ).order_by("-created_at")

    serializer = ConversationSerializer(
        user_conversations,
        many=True,
    )

    return Response(serializer.data, status=200)


# Handle GET and POST requests for conversations
# Handle GET and POST requests for conversations
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def conversations(request):

    if request.method == "GET":
        user_conversations = (
            Conversation.objects.filter(participant_1=request.user)
            | Conversation.objects.filter(participant_2=request.user)
        )

        user_conversations = user_conversations.select_related(
            "participant_1",
            "participant_2",
        ).order_by("-created_at")

        serializer = ConversationSerializer(
            user_conversations,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    # Handle POST directly instead of calling create_conversation()
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

    conversation = Conversation.objects.filter(
        participant_1=request.user,
        participant_2=other_user,
    ).first()

    if not conversation:
        conversation = Conversation.objects.filter(
            participant_1=other_user,
            participant_2=request.user,
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