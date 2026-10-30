from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

from .models import Conversation

User = get_user_model()


@database_sync_to_async
def set_user_online(user_id):
    User.objects.filter(id=user_id).update(is_online=True)


@database_sync_to_async
def set_user_offline(user_id):
    User.objects.filter(id=user_id).update(is_online=False)


@database_sync_to_async
def get_user_status(user_id):
    return User.objects.filter(id=user_id).values(
        "id",
        "username",
        "is_online",
    ).first()