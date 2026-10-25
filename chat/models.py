from django.db import models
from django.conf import settings

# Create your models here.

class Conversation(models.Model):
    participant_1 = models.ForeignKey(settings.AUTH_USER_MODEL,
                                      on_delete = models.CASCADE, related_name = "participant_1conversations")
    participant_2 = models.ForeignKey(
                                      settings.AUTH_USER_MODEL, 
                                      on_delete = models.CASCADE, related_name = "participant_2conversations"
                                      )

    created_at = models.DateTimeField(auto_created=True, auto_now_add=True)

    def __abs__(self):
        return f"cobversation {self.id}"

class Message(models.Model):
    conversation = models.ForeignKey(
                                            Conversation, 
                                            on_delete=models.CASCADE,
                                            related_name= "messages"
                                            )
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="sent_messages"
        )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True, auto_created=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message {self.id} in conversation {self.conversation.id}"
