from django.urls import path
from core.views import health_check, home


urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('', home, name='home'),
]
