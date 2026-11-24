from django.db import models
from django.conf import settings

# Create your models here.

class Conversation(models.Model):
    participant_1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_as_participant_1",
    )
    participant_2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_as_participant_2",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    is_group = models.BooleanField(default=False)

    def __str__(self):
        return f"Conversation {self.id}"

#  ===============================
#  Conversation Participant
#  ===============================

class ConversationParticipant(models.Model):

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        MODERATOR = "moderator", "Moderator"
        MEMBER = "member", "Member"

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="participants",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversation_memberships",
    )

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER,
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "user"],
                name="unique_conversation_participant",
            )
        ]

    def __str__(self):
        return f"{self.user} in Conversation {self.conversation.id}"


# ==============================
# Message Model
# ==============================
class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    is_delivered = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # Message editing fields
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)

    #replay
    reply_to = models.ForeignKey(
        "self",
        on_delete= models.SET_NULL,
        null = True,
        blank= True,
        related_name="replies"
    )
    is_forwarded = models.BooleanField(default=False)

    forwarded_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="forwarded_messages",
    )

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"Message {self.id} in conversation {self.conversation.id}"


# ==========================
# Message reaction model
# ===========================

class MessageReaction(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="reactions",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="message_reactions",
    )

    emoji = models.CharField(max_length=20)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["message", "user"],
                name="unique_user_message_reaction",
            )
        ]

    def __str__(self):
        return f"{self.user} reacted {self.emoji} to Message {self.message.id}"

# ===================================
# PinnedMessage Model
# ===================================
class PinnedMessage(models.Model):

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="pinned_messages",
    )

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="pinned_records",
    )

    pinned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pinned_messages",
    )

    pinned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "message"],
                name="unique_pinned_message_per_conversation",
            )
        ]

    def __str__(self):
        return f"Message {self.message.id} pinned in conversation {self.conversation.id}"

# =============================
# Messege Attachment
# =============================

class MessageAttachment(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="attachments",
    )

    file = models.FileField(
        upload_to="chat_attachments/",
    )

    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)
    file_size = models.PositiveBigIntegerField()

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name