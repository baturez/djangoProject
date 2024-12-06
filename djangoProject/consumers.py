import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from pymongo import MongoClient
import base64
from datetime import datetime

import os
from asgiref.sync import sync_to_async
MONGO_URI = 'mongodb+srv://batuhanfahri06:PezQB4OKaTHSEjFm@bartini.qyrro.mongodb.net/?retryWrites=true&w=majority&appName=bartini'
DATABASE_NAME = 'my_database'
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
messages_collection = db['messages']
group_messages_collection = db['group_messages']
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope['user'].is_authenticated:
            await self.close()  # If not authenticated, close the connection
            return

        self.username = self.scope['user'].username
        self.friend_username = self.scope['url_route']['kwargs']['friend_username']
        self.room_name = f'chat_{min(self.username, self.friend_username)}_{max(self.username, self.friend_username)}'
        self.room_group_name = f'chat_{self.room_name}'

        # Join group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Remove from group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        sender = text_data_json.get('sender')
        recipient = text_data_json.get('recipient')
        message = text_data_json.get('message')

        if 'fileData' in text_data_json:
            file_data = text_data_json['fileData']
            file_name = text_data_json['fileName']
            file_size = text_data_json['fileSize']

            file_data_bytes = base64.b64decode(file_data)
            file_path = os.path.join('uploads', file_name)
            with open(file_path, 'wb') as f:
                f.write(file_data_bytes)

            # Save file metadata
            file_data_entry = {
                'sender': sender,
                'recipient': recipient,
                'file_name': file_name,
                'file_size': file_size,
                'timestamp': timezone.now()
            }
            await database_sync_to_async(messages_collection.insert_one)(file_data_entry)

            # Acknowledge file receipt
            await self.send(text_data=json.dumps({
                'status': 'success',
                'fileName': file_name,
                'fileSize': file_size
            }))

        # Handle message
        if not sender or not recipient or not message:
            await self.send(text_data=json.dumps({
                'error': 'Eksik bilgi var.'
            }))
            return

        message_data = {
            'sender': sender,
            'recipient': recipient,
            'text': message,
            'timestamp': timezone.now()
        }
        await database_sync_to_async(messages_collection.insert_one)(message_data)

        # Broadcast message to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender,
                'recipient': recipient
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        recipient = event['recipient']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'recipient': recipient
        }))
class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = self.scope['url_route']['kwargs']['group_id']
        self.group_channel_name = f"group_{self.group_name}"

        # Gruba katıl
        await self.channel_layer.group_add(
            self.group_channel_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_channel_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender = text_data_json['sender']
        timestamp = text_data_json['timestamp']

        # Send message to group
        await self.channel_layer.group_send(
            self.group_channel_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender,
                'timestamp': timestamp
            }
        )

    # Receive message from group
    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        timestamp = event['timestamp']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message,
            'sender': sender,
            'timestamp': timestamp
        }))