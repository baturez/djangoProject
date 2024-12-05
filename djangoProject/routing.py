from django.urls import path
from djangoProject.consumers import ChatConsumer, GroupChatConsumer

websocket_urlpatterns = [
    path('ws/chat/<str:friend_username>/', ChatConsumer.as_asgi()),
    path('ws/group/<str:group_id>/', GroupChatConsumer.as_asgi()),
]
