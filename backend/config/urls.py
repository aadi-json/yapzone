from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
    path("api/chat/", include("chat.urls")),
    path("api-auth/", include("rest_framework.urls")),
    path("api/users/", include("users.urls")),
]