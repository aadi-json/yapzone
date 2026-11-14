from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def health_check(request):
    return Response({
    "status" : "healthy",
    "application" : "YapZone",
    "message" : "YapZone is running smoothly!",
})

@api_view(['GET'])
def home(request):
    return Response({
        "Message" : "Welcome to YapZone! This is the home endpoint.",
    })

