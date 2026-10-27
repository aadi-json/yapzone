from django.urls import path

from .views import (
    conversations,
    conversation_messages,
    create_message,   
)

urlpatterns = [
    path(
        "conversations/",
        conversations,
        name="conversations",
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
]

