import asyncio
import json

from django.utils import timezone

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Conversation, Message
from .connection_manager import connection_manager
from .presence import set_user_online, set_user_offline


class ChatConsumer(AsyncWebsocketConsumer):
    # ==========================================
    # CONNECTION
    # ==========================================

    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"
        self.typing_task = None

        user = self.scope["user"]

        if not user.is_authenticated:
            print("WebSocket rejected: unauthenticated user")
            await self.close()
            return

        self.user_id = user.id
        self.username = user.username

        is_participant = await self.check_participant(self.user_id)
        print(
            "WebSocket connection check:",
            f"user_id={self.user_id}",
            f"conversation_id={self.conversation_id}",
            f"is_participant={is_participant}",
        )

        if not is_participant:
            print("WebSocket rejected: user is not a conversation participant")
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        connection_count = await connection_manager.add_connection(
            self.user_id,
            self.channel_name,
        )

        if connection_count == 1:
            await set_user_online(self.user_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "presence_update",
                    "user_id": self.user_id,
                    "username": self.username,
                    "status": "online",
                },
            )

        await self.accept()

    # ==========================================
    # DISCONNECTION
    # ==========================================

    async def disconnect(self, close_code):
        if self.typing_task:
            self.typing_task.cancel()
            self.typing_task = None

        # Authentication or participant validation may reject the socket
        # before user_id is initialized or before it joins the group.
        if not hasattr(self, "user_id"):
            return

        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

        connection_count = await connection_manager.remove_connection(
            self.user_id,
            self.channel_name,
        )

        if connection_count == 0:
            await set_user_offline(self.user_id)

            if hasattr(self, "room_group_name"):
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "presence_update",
                        "user_id": self.user_id,
                        "username": self.username,
                        "status": "offline",
                    },
                )

    # ==========================================
    # RECEIVE WEBSOCKET EVENTS
    # ==========================================

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            await self.send_error("A JSON text message is required.")
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON.")
            return

        if not isinstance(data, dict):
            await self.send_error("The event must be a JSON object.")
            return

        event_type = data.get("type")

        if not isinstance(event_type, str):
            await self.send_error("Event type is required.")
            return

        # --------------------------------------
        # TYPING EVENT
        # --------------------------------------

        if event_type == "typing":
            is_typing = data.get("is_typing")

            if not isinstance(is_typing, bool):
                await self.send_error("is_typing must be a boolean.")
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_status",
                    "user_id": self.user_id,
                    "username": self.username,
                    "is_typing": is_typing,
                },
            )

            if self.typing_task:
                self.typing_task.cancel()

            if is_typing:
                self.typing_task = asyncio.create_task(self.typing_timeout())
            else:
                self.typing_task = None

            return

        # --------------------------------------
        # READ RECEIPT EVENT
        # --------------------------------------

        if event_type == "read":
            message_ids = data.get("message_ids")

            if not isinstance(message_ids, list) or not message_ids:
                await self.send_error("message_ids must be a non-empty list.")
                return

            if not all(
                isinstance(message_id, int)
                and not isinstance(message_id, bool)
                and message_id > 0
                for message_id in message_ids
            ):
                await self.send_error("All message IDs must be positive integers.")
                return

            updated_messages = await self.mark_messages_read(
                self.user_id,
                message_ids,
            )

            if updated_messages:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "read_receipt",
                        "message_ids": updated_messages,
                        "reader_id": self.user_id,
                        "reader_username": self.username,
                    },
                )

            return

        # --------------------------------------
        # EDIT MESSAGE EVENT
        # --------------------------------------

        if event_type == "edit_message":
            message_id = data.get("message_id")
            content = data.get("message")

            if (
                not isinstance(message_id, int)
                or isinstance(message_id, bool)
                or message_id <= 0
            ):
                await self.send_error("message_id must be a positive integer.")
                return

            if not isinstance(content, str) or not content.strip():
                await self.send_error("Edited message cannot be empty.")
                return

            content = content.strip()

            if len(content) > 5000:
                await self.send_error("Message cannot exceed 5000 characters.")
                return

            updated_message = await self.edit_message(
                message_id,
                self.user_id,
                content,
            )

            if not updated_message:
                await self.send_error(
                    "Message not found or you cannot edit this message."
                )
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "message_edited",
                    **updated_message,
                },
            )
            return

        # --------------------------------------
        # DELETE MESSAGE EVENT
        # --------------------------------------

        if event_type == "delete_message":
            message_id = data.get("message_id")

            if (
                not isinstance(message_id, int)
                or isinstance(message_id, bool)
                or message_id <= 0
            ):
                await self.send_error("message_id must be a positive integer.")
                return

            deleted = await self.delete_message(message_id, self.user_id)

            if not deleted:
                await self.send_error(
                    "Message not found or you cannot delete this message."
                )
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "message_deleted",
                    "message_id": message_id,
                    "deleted_by": self.user_id,
                },
            )
            return

        # --------------------------------------
        # NORMAL MESSAGE EVENT
        # --------------------------------------

        if event_type != "message":
            await self.send_error("Invalid event type.")
            return

        content = data.get("message")

        if not isinstance(content, str) or not content.strip():
            await self.send_error("Message cannot be empty.")
            return

        content = content.strip()

        if len(content) > 5000:
            await self.send_error("Message cannot exceed 5000 characters.")
            return

        # Get optional reply message ID
        reply_to_id = data.get("reply_to")

        if reply_to_id is not None:
            if (
                isinstance(reply_to_id, bool)
                or not isinstance(reply_to_id, int)
                or reply_to_id <= 0
            ):
                await self.send_error("Invalid reply message ID.")
                return

        # Save message
        message = await self.save_message(
            self.user_id,
            content,
            reply_to_id,
        )

        if message is None:
            await self.send_error(
                "Reply message not found in this conversation."
            )
            return

        # Broadcast message
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                **message,
            },
        )

    async def send_error(self, message: str) -> None:
        await self.send(
            text_data=json.dumps({
                    "type": "error",
                    "error": message,
                })
            )
    # ==========================================
    # AUTOMATIC TYPING TIMEOUT
    # ==========================================

    async def typing_timeout(self):
        try:
            await asyncio.sleep(3)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_status",
                    "user_id": self.user_id,
                    "username": self.username,
                    "is_typing": False,
                },
            )

            self.typing_task = None

        except asyncio.CancelledError:
            pass

    # ==========================================
    # DATABASE OPERATIONS
    # ==========================================

    @database_sync_to_async
    def check_participant(self, user_id):
        return Conversation.objects.filter(
            id=self.conversation_id,
            participant_1_id=user_id,
        ).exists() or Conversation.objects.filter(
            id=self.conversation_id,
            participant_2_id=user_id,
        ).exists()

    @database_sync_to_async
    def save_message(self, user_id, content, reply_to_id=None):

        reply_to = None

        if reply_to_id is not None:
            reply_to = Message.objects.filter(
                id=reply_to_id,
                conversation_id=self.conversation_id,
            ).select_related("sender").first()

            if not reply_to:
                return None

        message = Message.objects.create(
            conversation_id=self.conversation_id,
            sender_id=user_id,
            content=content,
            reply_to=reply_to,
        )

        reply_to_details = None

        if reply_to:
            reply_to_details = {
                "id": reply_to.id,
                "sender_username": reply_to.sender.username,
                "content": reply_to.content,
                "timestamp": reply_to.timestamp.isoformat(),
            }

        return {
            "message_id": message.id,
            "message": message.content,
            "sender": message.sender.username,
            "sender_id": message.sender_id,
            "timestamp": message.timestamp.isoformat(),
            "reply_to": reply_to.id if reply_to else None,
            "reply_to_details": reply_to_details,
        }

    @database_sync_to_async
    def edit_message(self, message_id, user_id, content):
        message = Message.objects.filter(
            id=message_id,
            conversation_id=self.conversation_id,
            sender_id=user_id,
        ).first()

        if not message:
            return None

        message.content = content
        message.is_edited = True
        message.edited_at = timezone.now()
        message.save(
            update_fields=["content", "is_edited", "edited_at"]
        )

        return {
            "message_id": message.id,
            "message": message.content,
            "sender_id": message.sender_id,
            "is_edited": message.is_edited,
            "edited_at": message.edited_at.isoformat(),
        }

    @database_sync_to_async
    def delete_message(self, message_id, user_id):
        deleted_count, _ = Message.objects.filter(
            id=message_id,
            conversation_id=self.conversation_id,
            sender_id=user_id,
        ).delete()

        return deleted_count > 0

    # ==========================================
    # MARK MESSAGE AS DELIVERED
    # ==========================================

    @database_sync_to_async
    def mark_message_delivered(self, message_id):
        message = Message.objects.filter(
            id=message_id,
            conversation_id=self.conversation_id,
            is_delivered=False,
        ).first()

        if not message:
            return False

        message.is_delivered = True
        message.delivered_at = timezone.now()
        message.save(update_fields=["is_delivered", "delivered_at"])

        return True

    # ==========================================
    # MARK MESSAGES AS READ
    # ==========================================

    @database_sync_to_async
    def mark_messages_read(self, user_id, message_ids):
        messages = Message.objects.filter(
            id__in=message_ids,
            conversation_id=self.conversation_id,
            is_read=False,
        ).exclude(sender_id=user_id)

        updated_ids = list(messages.values_list("id", flat=True))

        if updated_ids:
            messages.update(
                is_read=True,
                read_at=timezone.now(),
            )

        return updated_ids

    # ==========================================
    # GET MESSAGES SENT BY ORIGINAL SENDER
    # ==========================================

    @database_sync_to_async
    def get_message_ids_sent_by_user(self, message_ids, user_id):
        return list(
            Message.objects.filter(
                id__in=message_ids,
                conversation_id=self.conversation_id,
                sender_id=user_id,
            ).values_list("id", flat=True)
        )

    # ==========================================
    # WEBSOCKET MESSAGE HANDLERS
    # ==========================================

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message",
                    "message_id": event["message_id"],
                    "message": event["message"],
                    "sender": event["sender"],
                    "sender_id": event["sender_id"],
                    "timestamp": event["timestamp"],
                    "reply_to": event["reply_to"],
                    "reply_to_details": event["reply_to_details"],
                    "is_forwarded": event.get("is_forwarded", False),
                    "forwarded_from": event.get("forwarded_from"),
                    "forwarded_from_username": event.get("forwarded_from_username"),
                }
            )
        )

        # Only the recipient marks the message as delivered.
        if event["sender_id"] == self.user_id:
            return

        delivered = await self.mark_message_delivered(event["message_id"])

        if delivered:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "delivery_receipt",
                    "message_id": event["message_id"],
                    "sender_id": event["sender_id"],
                },
            )

    async def message_edited(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message_edited",
                    "message_id": event["message_id"],
                    "message": event["message"],
                    "sender_id": event["sender_id"],
                    "is_edited": event["is_edited"],
                    "edited_at": event["edited_at"],
                }
            )
        )

    async def message_deleted(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message_deleted",
                    "message_id": event["message_id"],
                    "deleted_by": event["deleted_by"],
                }
            )
        )

    # ==========================================
    # DELIVERY RECEIPT HANDLER
    # ==========================================

    async def delivery_receipt(self, event):
        if self.user_id != event["sender_id"]:
            return

        await self.send(
            text_data=json.dumps(
                {
                    "type": "delivery_receipt",
                    "message_id": event["message_id"],
                    "status": "delivered",
                }
            )
        )

    # ==========================================
    # READ RECEIPT HANDLER
    # ==========================================

    async def read_receipt(self, event):
        message_ids = await self.get_message_ids_sent_by_user(
            event["message_ids"],
            self.user_id,
        )

        if not message_ids:
            return

        await self.send(
            text_data=json.dumps(
                {
                    "type": "read_receipt",
                    "message_ids": message_ids,
                    "reader_id": event["reader_id"],
                    "reader_username": event["reader_username"],
                    "status": "read",
                }
            )
        )

    # ==========================================
    # PRESENCE HANDLER
    # ==========================================

    async def presence_update(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "presence",
                    "user_id": event["user_id"],
                    "username": event["username"],
                    "status": event["status"],
                }
            )
        )

    # ==========================================
    # TYPING STATUS HANDLER
    # ==========================================

    async def typing_status(self, event):
        if event["user_id"] == self.user_id:
            return

        await self.send(
            text_data=json.dumps(
                {
                    "type": "typing",
                    "user_id": event["user_id"],
                    "username": event["username"],
                    "is_typing": event["is_typing"],
                }
            )
        )
    # ===========================
    # Message Pinned Event
    # ===========================

    async def message_pinned(self, event):

        await self.send(
            text_data=json.dumps(
                {
                    "type": "message_pinned",
                    "message_id": event["message_id"],
                    "pinned_by": event["pinned_by"],
                    "pinned_by_username": event["pinned_by_username"],
                    "pinned_at": event["pinned_at"],
                }
            )
        )

    # ===========================
    # Message Unpinned Event
    # ===========================

    async def message_unpinned(self, event):

        await self.send(
            text_data=json.dumps(
                {
                    "type": "message_unpinned",
                    "message_id": event["message_id"],
                    "unpinned_by": event["unpinned_by"],
                    "unpinned_by_username": event["unpinned_by_username"],
                }
            )
        )
