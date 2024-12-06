from django.urls import path
from djangoProject.consumers import ChatConsumer, GroupChatConsumer

websocket_urlpatterns = [
    path('ws/chat/<str:group_name>/', ChatConsumer.as_asgi()),
    path('ws/group/<str:group_id>/', GroupChatConsumer.as_asgi()),
]
