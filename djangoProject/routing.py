from django.urls import path
from djangoProject.consumers import ChatConsumer, GroupChatConsumer
from django.urls import re_path
from .consumers import ChatRoomConsumer

websocket_urlpatterns = [
    path('ws/chat/<str:friend_username>/', ChatConsumer.as_asgi()),
    path('ws/group/<str:group_id>/', GroupChatConsumer.as_asgi()),
    re_path(r'ws/chat_room/(?P<room_name>\w+)/$', ChatRoomConsumer.as_asgi()),

]
