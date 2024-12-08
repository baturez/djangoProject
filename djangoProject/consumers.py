import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from pymongo import MongoClient
import base64
from datetime import datetime

import os
from asgiref.sync import sync_to_async

from djangoProject import settings

MONGO_URI = 'mongodb+srv://batuhanfahri06:PezQB4OKaTHSEjFm@bartini.qyrro.mongodb.net/?retryWrites=true&w=majority&appName=bartini'
DATABASE_NAME = 'my_database'
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
messages_collection = db['messages']
group_messages_collection = db['group_messages']


# WebSocket consumer
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.username = self.scope['user'].username
        self.friend_username = self.scope['url_route']['kwargs']['friend_username']
        self.room_name = f'chat_{min(self.username, self.friend_username)}_{max(self.username, self.friend_username)}'
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        json_data = json.loads(text_data)
        message_content = json_data.get('message')
        sender = json_data.get('sender')
        recipient = json_data.get('recipient')
        file_name = json_data.get('fileName')
        file_size = json_data.get('fileSize')
        file_type = json_data.get('fileType')
        file_data = json_data.get('fileData')

        # Handle file upload
        if file_data:
            message = await save_file_to_mongo(sender, recipient, file_name, file_size, file_type, file_data)

            # Send file message to WebSocket
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': f'{sender} sent a file: {file_name}',
                    'file_name': file_name,
                    'file_size': file_size,
                    'file_type': file_type,
                    'file_data': file_data
                }
            )

        # Handle text message
        if message_content:
            # Save message to MongoDB
            message_data = {
                'sender': sender,
                'recipient': recipient,
                'text': message_content,
                'timestamp': timezone.now()
            }
            messages_collection.insert_one(message_data)  # Save message to MongoDB

            # Send message to WebSocket
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_content,
                    'sender': sender,
                    'recipient': recipient
                }
            )

        # Handle file downloaded (for deletion)
        elif json_data.get('type') == 'file_downloaded':
            file_name = json_data.get('file_name')

            # Delete file from MongoDB
            await self.delete_file_from_mongo(file_name)

            # Notify the client that the file is deleted
            await self.send(text_data=json.dumps({
                'status': 'success',
                'message': f'File {file_name} has been deleted after download.'
            }))

    async def chat_message(self, event):
        message = event['message']
        sender = event.get('sender', None)
        recipient = event.get('recipient', None)
        file_name = event.get('file_name', None)
        file_size = event.get('file_size', None)
        file_type = event.get('file_type', None)
        file_data = event.get('file_data', None)

        # Send message over WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'recipient': recipient,
            'file_name': file_name,
            'file_size': file_size,
            'file_type': file_type,
            'file_data': file_data
        }))

    # Delete file from MongoDB
    @database_sync_to_async
    def delete_file_from_mongo(self, file_name):
        try:
            # MongoDB'den dosya verisini sil
            file_data_entry = messages_collection.find_one_and_delete(
                {'file_name': file_name}
            )

            if file_data_entry:
                print(f"File {file_name} deleted from MongoDB.")
            else:
                print(f"File {file_name} not found in MongoDB.")
        except Exception as e:
            print(f"Error deleting file from MongoDB: {e}")


# MongoDB'ye dosya kaydetme işlemi
@database_sync_to_async
def save_file_to_mongo(sender, recipient, file_name, file_size, file_type, file_data):
    # MongoDB'ye kaydedilecek mesaj verisi
    message = {
        'sender': sender,
        'recipient': recipient,
        'file_name': file_name,
        'file_size': file_size,
        'file_type': file_type,
        'file_data': file_data,  # Base64 encoded file data
        'timestamp': timezone.now()
    }

    # Save message to MongoDB
    messages_collection.insert_one(message)

    return message
class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = self.scope['url_route']['kwargs']['group_id']
        self.group_channel_name = f"group_{self.group_name}"

        # Join group
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