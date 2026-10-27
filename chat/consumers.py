import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Conversation, Message


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"][
            "conversation_id"
        ]

        self.room_group_name = f"chat_{self.conversation_id}"

        # Get the authenticated Django user.
        user = self.scope["user"]

        # Reject anonymous users.
        if not user.is_authenticated:
            await self.close()
            return

        # Verify that the user belongs to this conversation.
        is_participant = await self.check_participant(user.id)

        if not is_participant:
            await self.close()
            return

        # Join the conversation group.
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "error": "Invalid JSON."
            }))
            return

        content = data.get("message")

        if not isinstance(content, str) or not content.strip():
            await self.send(text_data=json.dumps({
                "error": "Message cannot be empty."
            }))
            return

        content = content.strip()

        if len(content) > 5000:
            await self.send(text_data=json.dumps({
                "error": "Message cannot exceed 5000 characters."
            }))
            return

        # Save the message using the authenticated user.
        message = await self.save_message(
            self.scope["user"].id,
            content,
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                **message,
            },
        )

    @database_sync_to_async
    def check_participant(self, user_id):
        return Conversation.objects.filter(
            id=self.conversation_id,
        ).filter(
            participant_1_id=user_id,
        ).exists() or Conversation.objects.filter(
            id=self.conversation_id,
            participant_2_id=user_id,
        ).exists()

    @database_sync_to_async
    def save_message(self, user_id, content):
        message = Message.objects.create(
            conversation_id=self.conversation_id,
            sender_id=user_id,
            content=content,
        )

        return {
            "message_id": message.id,
            "message": message.content,
            "sender": message.sender.username,
            "timestamp": message.timestamp.isoformat(),
        }

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message_id": event["message_id"],
            "message": event["message"],
            "sender": event["sender"],
            "timestamp": event["timestamp"],
        }))