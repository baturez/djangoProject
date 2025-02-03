import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from pymongo import MongoClient
import base64
from datetime import datetime
from asgiref.sync import sync_to_async
MONGO_URI = 'mongodb://localhost:27017/my_database'
#MONGO_URI = 'mongodb+srv://batuhanfahri06:PezQB4OKaTHSEjFm@bartini.qyrro.mongodb.net/?retryWrites=true&w=majority&appName=bartini'
DATABASE_NAME = 'my_database'
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
messages_collection = db['messages']
group_messages_collection = db['group_messages']
notifications_collection = db['notifications']
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

        if file_data:
            message = await save_file_to_mongo(sender, recipient, file_name, file_size, file_type, file_data)

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

        if message_content:
            message_data = {
                'sender': sender,
                'recipient': recipient,
                'text': message_content,
                'timestamp': timezone.now(),
                'read': False
            }
            messages_collection.insert_one(message_data)

            await self.create_notification(recipient, sender, message_content)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_content,
                    'sender': sender,
                    'recipient': recipient,
                    'notification': 'new_message'
                }
            )

        elif json_data.get('type') == 'file_downloaded':
            file_name = json_data.get('file_name')

            await self.delete_file_from_mongo(file_name)

            await self.send(text_data=json.dumps({
                'status': 'success',
                'message': f'File {file_name} has been deleted after download.'
            }))

        elif json_data.get('type') == 'mark_as_read':
            message_id = json_data.get('message_id')

            await self.mark_message_as_read(message_id)

            await self.send(text_data=json.dumps({
                'status': 'success',
                'message': 'Message marked as read.'
            }))

    async def chat_message(self, event):
        message = event['message']
        sender = event.get('sender', None)
        recipient = event.get('recipient', None)
        file_name = event.get('file_name', None)
        file_size = event.get('file_size', None)
        file_type = event.get('file_type', None)
        file_data = event.get('file_data', None)

        notification_message = f"{sender} sent you a new message!"

        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'recipient': recipient,
            'file_name': file_name,
            'file_size': file_size,
            'file_type': file_type,
            'file_data': file_data,
            'notification': notification_message
        }))

    @sync_to_async
    def create_notification(self, receiver, sender, message):
        unread_message = messages_collection.find_one({
            'recipient': receiver,
            'read': False
        })

        if unread_message:
            notifications_collection.insert_one({

                "sender": sender,
                "message": f"New message from {sender}: {message}",
                "timestamp": datetime.now(),

            })

    @sync_to_async
    def mark_message_as_read(self, message_id):
        messages_collection.update_one(
            {'_id': message_id},
            {'$set': {'read': True}}
        )

    @database_sync_to_async
    def delete_file_from_mongo(self, file_name):
        try:
            file_data_entry = messages_collection.find_one_and_delete(
                {'file_name': file_name}
            )

            if file_data_entry:
                print(f"File {file_name} deleted from MongoDB.")
            else:
                print(f"File {file_name} not found in MongoDB.")
        except Exception as e:
            print(f"Error deleting file from MongoDB: {e}")


@sync_to_async
def save_file_to_mongo(sender, recipient, file_name, file_size, file_type, file_data):
    file_entry = {
        "sender": sender,
        "recipient": recipient,
        "file_name": file_name,
        "file_size": file_size,
        "file_type": file_type,
        "file_data": file_data,
        "timestamp": datetime.now(),
        "read": False
    }
    messages_collection.insert_one(file_entry)
    return file_entry
class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = self.scope['url_route']['kwargs']['group_id']
        self.group_channel_name = f"group_{self.group_name}"

        await self.channel_layer.group_add(
            self.group_channel_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_channel_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender = text_data_json['sender']
        timestamp = text_data_json['timestamp']

        await self.channel_layer.group_send(
            self.group_channel_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender,
                'timestamp': timestamp
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        timestamp = event['timestamp']

        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message,
            'sender': sender,
            'timestamp': timestamp
        }))




class ChatRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
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
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender = text_data_json['sender']

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender
        }))