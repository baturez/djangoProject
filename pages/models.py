# models.py

from django.db import models
from django.contrib.auth.models import User
from djongo import models


class Group(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)  # Grup oluşturulma tarihi
    updated_at = models.DateTimeField(auto_now=True)      # Grup güncellenme tarihi

    def __str__(self):
        return self.name

class GroupJoinRequest(models.Model):
    group = models.ForeignKey(Group, related_name='join_requests', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)  # İstek oluşturulma tarihi

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
    content = models.TextField()  # Mesaj içeriği
    timestamp = models.DateTimeField(auto_now_add=True)  # Mesajın gönderildiği zaman

    def __str__(self):
        return self.content

class UserProfile(models.Model):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField()
    profile_picture = models.URLField(blank=True, null=True)

