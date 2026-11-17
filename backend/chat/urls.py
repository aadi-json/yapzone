from django.urls import path
from .views import (
    conversations,
    create_conversation,
    conversation_messages,
    create_message,
    add_message_reaction,
    forward_message,
)

urlpatterns = [
    path(
        "conversations/",
        conversations,
        name="conversations",
    ),
    path(
        "conversations/create/",
        create_conversation,
        name="create-conversation",
    ),
    path(
        "conversations/<int:conversation_id>/messages/",
        conversation_messages,
        name="conversation-messages",
    ),
    path(
        "conversations/<int:conversation_id>/messages/send/",
        create_message,
        name="create-message",
    ),
    path(
        "conversations/<int:conversation_id>/messages/<int:message_id>/reactions/",
        add_message_reaction,
        name="add-message-reaction",
    ),
    path(
    "conversations/<int:conversation_id>/messages/<int:message_id>/forward/",
    forward_message,
    name="forward-message",
    ),
]

