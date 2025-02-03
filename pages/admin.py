from django.contrib import admin
from pymongo import MongoClient
from bson import ObjectId
from .models import User
MONGO_URI = 'mongodb://localhost:27017/my_database'
USER_COLLECTION = 'users'
DATABASE_NAME = 'my_database'
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
user_collection = db[USER_COLLECTION]

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_banned')
    list_filter = ('is_banned',)
    search_fields = ('username', 'email')
    actions = ['ban_users', 'unban_users']
    def ban_users(self, request, queryset):
        selected_ids = request.POST.getlist('_selected_action')
        if not selected_ids:
            self.message_user(request, "Seçilen kullanıcılar bulunamadı.")
            return
        object_ids = [ObjectId(id) for id in selected_ids]
        result = user_collection.update_many(
            {'_id': {'$in': object_ids}},
            {'$set': {'is_banned': True}}
        )

        self.message_user(request, f"{result.modified_count} kullanıcı başarıyla yasaklandı.")
    def unban_users(self, request, queryset):
        selected_ids = request.POST.getlist('_selected_action')
        if not selected_ids:
            self.message_user(request, "Seçilen kullanıcılar bulunamadı.")
            return
        object_ids = [ObjectId(id) for id in selected_ids]

        result = user_collection.update_many(
            {'_id': {'$in': object_ids}},
            {'$set': {'is_banned': False}}
        )
        self.message_user(request, f"{result.modified_count} kullanıcının yasağı kaldırıldı.")
admin.site.register(User, UserAdmin)
