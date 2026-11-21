from django.urls import path
from .views import (
    conversations,
    create_conversation,
    conversation_messages,
    create_message,
    add_message_reaction,
    forward_message,
    pin_message,
    unpin_message,
    get_pinned_messages,
    search_messages,
    upload_attachment,
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
        # Pin message
    path(
        "conversations/<int:conversation_id>/messages/<int:message_id>/pin/",
        pin_message,
        name="pin-message",
    ),

    # Unpin message
    path(
        "conversations/<int:conversation_id>/messages/<int:message_id>/unpin/",
        unpin_message,
        name="unpin-message",
    ),

    # Get pinned messages
    path(
        "conversations/<int:conversation_id>/pinned-messages/",
        get_pinned_messages,
        name="pinned-messages",
    ),
    # Search messages
    path(
        "messages/search/",
        search_messages,
        name="search-messages",
    ),
    path(
    "conversations/<int:conversation_id>/messages/<int:message_id>/attachments/",
    upload_attachment,
    name="upload-attachment",
    ),
]

