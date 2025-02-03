import mongoengine
from django.contrib.auth.models import User
from pymongo import MongoClient
from djongo import models
from django.conf import settings
MONGO_URI = 'mongodb://localhost:27017/my_database'
# MONGO_URI = 'mongodb+srv://batuhanfahri06:PezQB4OKaTHSEjFm@bartini.qyrro.mongodb.net/<database>?retryWrites=true&w=majority&readPreference=secondaryPreferred'
DATABASE_NAME = 'my_database'
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
USER_COLLECTION = 'users'
mongoengine.connect(db=settings.DATABASE_NAME, host=settings.MONGO_URI)
class Group(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class GroupJoinRequest(models.Model):
    group = models.ForeignKey(Group, related_name='join_requests', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.group.name}"

class ChatMessage(models.Model):
        sender = models.CharField(max_length=100)
        recipient = models.CharField(max_length=100)
        message = models.TextField()
        timestamp = models.DateTimeField(auto_now_add=True)

        def __str__(self):
            return f"Message from {self.sender} to {self.recipient}"

        class Meta:
            ordering = ['timestamp']

class Message(models.Model):
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content



class User(models.Model):
    _id = models.ObjectIdField()
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    is_banned = models.BooleanField(default=False)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username