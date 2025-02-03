import base64
import os

from django.core.cache import cache
from django.core.mail import EmailMessage
from datetime import datetime,timedelta
from flask import Flask, request, jsonify
from channels.db import database_sync_to_async
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.shortcuts import redirect
from pymongo import MongoClient, DESCENDING
import bcrypt
from django.core.files.storage import FileSystemStorage
import pytz
from django.utils import timezone
import random
import json
from django.shortcuts import render
from bson.objectid import ObjectId
from pymongo.errors import ConnectionFailure
from django.views.decorators.csrf import csrf_exempt
import time
from django.contrib.auth import logout as auth_logout
from django.http import JsonResponse
from django.contrib import messages
from django.template.loader import render_to_string
import uuid
MONGO_URI = 'mongodb://localhost:27017/my_database'
# MONGO_URI = 'mongodb+srv://batuhanfahri06:PezQB4OKaTHSEjFm@bartini.qyrro.mongodb.net/<database>?retryWrites=true&w=majority&readPreference=secondaryPreferred'
DATABASE_NAME = 'my_database'
USER_COLLECTION = 'users'
POST_COLLECTION = 'posts'
GROUP_COLLECTION = 'groups'
TOPIC_COLLECTION = 'topics'
TOPIC_COMMENT_COLLECTION = 'topic_comments'
COMMENT_COLLECTION = 'comments'
JOIN_REQUEST_COLLECTION = 'join_request'
FRIEND_REQUEST_COLLECTION = 'friend_requests'
STORY_COLLECTION = 'stories'

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
messages_collection = db['messages']
MEMBERSHIP_REQUEST_COLLECTION = 'membership_requests'
story_collection = db['stories']

app = Flask(__name__)
@csrf_exempt
def index(request):
    return render(request, "index.html")
def privacy_policy(request):
    return render(request, "kvkk.html")
@csrf_exempt
def signup(request):
    return render(request, "sign_up.html")
def post_view(request, post_id):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    username = request.session.get('username')

    post_collection = db[POST_COLLECTION]
    post = post_collection.find_one({"_id": ObjectId(post_id)})
    popular_posts = post_collection.find().sort("likes", -1).limit(3)
    popular_posts = list(popular_posts)
    print(post)
    if post:
        post['_id'] = str(post['_id'])

        post_user = db[USER_COLLECTION].find_one({'username': post.get('username')})
        post['profile_picture'] = post_user.get('profile_picture', 'default.png') if post_user else 'default.png'
        context = get_common_context(username, db)
        context.update({
            'post': post,
            'popular_posts': popular_posts,

        })
        if 'comments' in post:
            for comment in post['comments']:
                comment['created_at'] = comment.get('created_at', 'Unknown')

        return render(request, 'post_view.html', context)
    else:
        return render(request, 'post_view.html', {'error': 'Post not found.'})
def chat_rooms(request):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    username = request.session.get('username')
    context = get_common_context(username, db)

    context.update({
        'rooms': range(1, 11),
        'username': username
    })

    return render(request, "chat_rooms.html", context)
def get_static_context(db):
    cached_context = cache.get('static_context')
    if cached_context:
        return cached_context

    group_collection = db[GROUP_COLLECTION]
    groups = list(group_collection.find())
    topics = list(db[TOPIC_COLLECTION].find().sort('like', DESCENDING).limit(3))
    for topic in topics:
        topic['_id'] = str(topic['_id'])

    static_context = {
        'groups': groups,
        'topics': topics,
    }
    cache.set('static_context', static_context, timeout=600)
    return static_context
def home(request):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]

    username = request.session.get('username')
    user_collection = db[USER_COLLECTION]
    post_collection = db[POST_COLLECTION]
    group_collection = db[GROUP_COLLECTION]

    current_user = user_collection.find_one({'username': username})
    friends = get_friends(current_user) if current_user else []
    profile_picture = current_user.get('profile_picture', 'default.png') if current_user else 'default.png'

    posts = post_collection.find().sort("created_at", -1)
    posts_with_pictures = []
    for post in posts:
        post['_id'] = str(post['_id'])
        post_user = user_collection.find_one({'username': post['username']})
        post['profile_picture'] = post_user.get('profile_picture', 'default.png') if post_user else 'default.png'
        posts_with_pictures.append(post)

    # Popüler gönderiler
    popular_posts = post_collection.find().sort("likes", -1).limit(3)
    popular_posts = list(popular_posts)
    for post in popular_posts:
        post['_id'] = str(post['_id'])

    # Gruplar ve konular
    groups = group_collection.find()
    topics = db[TOPIC_COLLECTION].find().sort('like', -1).limit(3)
    topics = list(topics)
    for topic in topics:
        topic['_id'] = str(topic['_id'])
        context = get_common_context(username, db)
    context = get_common_context(username, db)
    return render(request, 'home_page.html', context)
def get_common_context(username, db):
    user_collection = db[USER_COLLECTION]
    post_collection = db[POST_COLLECTION]
    group_collection = db[GROUP_COLLECTION]
    topic_collection = db[TOPIC_COLLECTION]
    user = user_collection.find_one({"username": username})
    stories = list(story_collection.find({}, {'_id': 0}))
    current_user = user_collection.find_one({'username': username})
    friends = get_friends(current_user) if current_user else []
    profile_picture = current_user.get('profile_picture', 'default.png') if current_user else 'default.png'
    pp = user_collection.find_one({"profile_picture": user['profile_picture']})

    posts = list(post_collection.find().sort("created_at", -1))
    user_usernames = {post['username'] for post in posts}
    users = {user['username']: user for user in user_collection.find({'username': {'$in': list(user_usernames)}})}


    for post in posts:
        post['_id'] = str(post['_id'])
        user = users.get(post['username'])
        post['profile_picture'] = user.get('profile_picture', 'default.png') if user else 'default.png'

    popular_posts = list(post_collection.find().sort("likes", -1).limit(3))
    for post in popular_posts:
        post['_id'] = str(post['_id'])

    groups = list(group_collection.find())
    topics = list(topic_collection.find().sort('like', -1).limit(3))
    for topic in topics:
        topic['_id'] = str(topic['_id'])

    return {
        'posts': posts,
        'groups': groups,
        'current_user': current_user,
        'friends': friends,
        'topics': topics,
        'popular_posts': popular_posts,
        'profile_picture': profile_picture,
        'username': username,
        'pp':pp,
        'stories':stories,

    }
def topic(request):
    username = request.session.get('username')
    context = get_common_context(username, db)
    context.update({

    })
    return render(request, "topics.html",context)
def get_topics(request):
    if request.method == 'GET':
        try:
            topics = list(db[TOPIC_COLLECTION].find())

            if not topics:
                return JsonResponse({'error': 'No topics found.'}, status=404)

            for topic in topics:
                topic['_id'] = str(topic['_id'])
                topic['likes_count'] = topic.get('like', 0)
                topic['dislikes_count'] = topic.get('dislike', 0)
                topic['comment_count'] = topic.get('comment_count', 0)

            return JsonResponse({'topics': topics}, safe=False)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
def list_topics(request):
    topics = db[TOPIC_COLLECTION].find().sort('like', -1).limit(3)
    for topic in topics:
        topic['_id'] = str(topic['_id'])
    return render(request, 'topics.html', {'topics': topics})
@csrf_exempt
def create_topic(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title')
            description = data.get('description')
            username = request.session.get('username')

            new_topic = {
                'title': title,
                'description': description,
                'created_at': datetime.now(),
                'username': username,
                'comments': [],
                'comment_count': 0,
                'like': 0,
                'dislike': 0
            }

            result = db[TOPIC_COLLECTION].insert_one(new_topic)
            topic_id = str(result.inserted_id)

            return JsonResponse({
                'success': True,
                'message': 'Topic created successfully!',
                'topic_id': topic_id,
                'comment_count': 0,
                'like': 0,
                'dislike': 0
            }, status=201)

        except Exception as e:
            return JsonResponse({'success': False, 'error_message': str(e)}, status=400)
@csrf_exempt
def add_comment_topic(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            topic_id = data.get('topic_id')
            comment_text = data.get('comment_text')
            commenter = request.session.get('username')

            if not topic_id or not comment_text:
                return JsonResponse({'error': 'Topic ID and comment text are required.'}, status=400)

            new_comment = {
                'topic_id': ObjectId(topic_id),
                'comment_text': comment_text,
                'created_at': datetime.now(),
                'commenter': commenter
            }

            db['topic_comments'].insert_one(new_comment)

            db['topics'].update_one(
                {'_id': ObjectId(topic_id)},
                {'$inc': {'comment_count': 1}}
            )

            return JsonResponse({'success': True, 'message': 'Comment added successfully!'}, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
@csrf_exempt
def get_comments_for_topic(request, topic_id):
    if request.method == 'GET':
        try:
            comments = db['topic_comments'].find({'topic_id': ObjectId(topic_id)})
            comment_list = [{'comment_text': comment['comment_text'], 'created_at': comment['created_at'], 'commenter': comment['commenter']} for comment in comments]
            return JsonResponse({'comments': comment_list}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
@csrf_exempt
def like_topic(request, topic_id):
    if request.method == 'POST':
        try:
            username = request.session.get('username')
            if not username:
                return JsonResponse({'success': False, 'error_message': 'User not logged in.'}, status=403)

            topic = db[TOPIC_COLLECTION].find_one({'_id': ObjectId(topic_id)})
            if not topic:
                return JsonResponse({'success': False, 'error_message': 'Topic not found.'}, status=404)

            user_likes = topic.get('user_likes', {})

            if user_likes.get(username) == 'liked':
                likes = topic.get('like', 0) - 1
                user_likes.pop(username)
            else:
                dislikes = topic.get('dislike', 0)
                if user_likes.get(username) == 'disliked':
                    dislikes -= 1

                likes = topic.get('like', 0) + 1
                user_likes[username] = 'liked'

                db[TOPIC_COLLECTION].update_one(
                    {'_id': ObjectId(topic_id)},
                    {'$set': {'dislike': dislikes}}
                )

            db[TOPIC_COLLECTION].update_one(
                {'_id': ObjectId(topic_id)},
                {'$set': {'like': likes, 'user_likes': user_likes}}
            )

            return JsonResponse({'success': True, 'message': 'Like toggled successfully!', 'like': likes, 'dislike': dislikes}, status=200)

        except Exception as e:
            return JsonResponse({'success': False, 'error_message': str(e)}, status=400)
@csrf_exempt
def dislike_topic(request, topic_id):
    if request.method == 'POST':
        try:
            username = request.session.get('username')
            if not username:
                return JsonResponse({'success': False, 'error_message': 'User not logged in.'}, status=403)

            topic = db[TOPIC_COLLECTION].find_one({'_id': ObjectId(topic_id)})
            if not topic:
                return JsonResponse({'success': False, 'error_message': 'Topic not found.'}, status=404)

            user_likes = topic.get('user_likes', {})

            if user_likes.get(username) == 'disliked':
                dislikes = topic.get('dislike', 0) - 1
                user_likes.pop(username)
            else:
                likes = topic.get('like', 0)
                if user_likes.get(username) == 'liked':
                    likes -= 1

                dislikes = topic.get('dislike', 0) + 1
                user_likes[username] = 'disliked'

                db[TOPIC_COLLECTION].update_one(
                    {'_id': ObjectId(topic_id)},
                    {'$set': {'like': likes}}
                )

            db[TOPIC_COLLECTION].update_one(
                {'_id': ObjectId(topic_id)},
                {'$set': {'dislike': dislikes, 'user_likes': user_likes}}
            )

            return JsonResponse({'success': True, 'message': 'Dislike toggled successfully!', 'like': likes, 'dislike': dislikes}, status=200)

        except Exception as e:
            return JsonResponse({'success': False, 'error_message': str(e)}, status=400)
def verify_email(request, token):
    user_collection = db[USER_COLLECTION]
    user = user_collection.find_one({"verification_token": token})

    if user:
        user_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"is_verified": True}},
        )
        success_message = "Hesabınız başarıyla doğrulandı!"
        return render(request, 'sign_up.html', {'success_message': success_message})
    else:
        error_message = "Geçersiz doğrulama bağlantısı!"
        return render(request, 'sign_up.html', {'error_message': error_message})
@csrf_exempt
def register(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        user_collection = db[USER_COLLECTION]
        existing_user = user_collection.find_one({"$or": [{"email": email}, {"username": username}]})

        if existing_user:
            if existing_user.get("email") == email:
                error_message = "Bu e-posta adresi zaten kayıtlı."
            elif existing_user.get("username") == username:
                error_message = "Bu kullanıcı adı zaten kullanılıyor."
            return render(request, 'sign_up.html', {'error_message': error_message})

        ip_address = get_client_ip(request)

        if save_to_mongo(email, username, password, ip_address, is_banned=False):
            success_message = "Kayıt işlemi başarılı! Lütfen e-posta adresinizi doğrulayın."

            token = str(uuid.uuid4())
            user_collection.update_one(
                {"email": email},
                {"$set": {"verification_token": token}}
            )

            verification_link = f"http://localhost:8000/verify/{token}"

            subject = "E-posta Doğrulaması"

            message = render_to_string('email/verify_email.html', {
                'username': username,
                'verification_link': verification_link,
            })

            email_message = EmailMessage(
                subject,
                message,
                'no-reply@bartini.com',
                [email]
            )
            email_message.content_subtype = "html"
            email_message.send()

            return render(request, 'sign_up.html', {'success_message': success_message})
        else:
            error_message = "Kayıt işlemi sırasında bir hata oluştu."
            return render(request, 'sign_up.html', {'error_message': error_message})

    return render(request, 'sign_up.html')
@csrf_exempt
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password').encode('utf-8')

        try:
            client = MongoClient(MONGO_URI)
            db = client[DATABASE_NAME]
            collection = db[USER_COLLECTION]

            user = collection.find_one({"username": username})

            if user:
                if user.get('is_banned', False):
                    error_message = "Hesabınız yasaklanmış. Lütfen destek ekibiyle iletişime geçin."
                    return render(request, 'index.html', {'error_message': error_message})

                if not bcrypt.checkpw(password, user['password']):
                    error_message = "Kullanıcı adı veya şifre yanlış!"
                    return render(request, 'index.html', {'error_message': error_message})

                if not user.get('is_verified', False):
                    error_message = "Hesabınızı doğrulamadınız. Lütfen e-posta adresinizi kontrol edin."
                    return render(request, 'index.html', {'error_message': error_message})

                request.session['username'] = username
                return redirect('/home')
            else:
                error_message = "Kullanıcı adı veya şifre yanlış!"
                return render(request, 'index.html', {'error_message': error_message})

        except ConnectionFailure:
            error_message = "Veritabanı bağlantısında hata oluştu!"
            return render(request, 'index.html', {'error_message': error_message})
        except Exception as e:
            error_message = f"Beklenmeyen bir hata oluştu: {str(e)}"
            return render(request, 'index.html', {'error_message': error_message})

    return render(request, 'index.html')
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
def save_to_mongo(email, username, password, ip_address, is_banned=False):
    try:
        client = MongoClient(MONGO_URI)
        client.server_info()

        db = client[DATABASE_NAME]
        collection = db[USER_COLLECTION]

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        default_profile_picture = f"{random.randint(1, 6)}.png"
        user_data = {
            "email": email,
            "username": username,
            "password": hashed_password,
            "friends": [],
            "profile_picture": default_profile_picture,
            "ip_address": ip_address,
            "is_banned": is_banned,
            'created_at': datetime.now(),
        }

        result = collection.insert_one(user_data)
        collection.update_one(
            {"_id": result.inserted_id},
            {"$set": {"id": result.inserted_id}}
        )
        return result.acknowledged

    except ConnectionFailure as e:
        print(f"MongoDB bağlantı hatası: {e}")
        return False
    except Exception as e:
        print(f"Beklenmeyen bir hata oluştu: {e}")
        return False
def upload_profile_picture(request):
    if request.method == 'POST' and request.FILES['profile_picture']:
        profile_picture = request.FILES['profile_picture']

        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        filename = fs.save(profile_picture.name, profile_picture)
        file_url = filename

        username = request.session.get('username')

        if username:
            client = MongoClient(MONGO_URI)
            db = client[DATABASE_NAME]
            user_collection = db[USER_COLLECTION]

            user_collection.update_one(
                {"username": username},
                {"$set": {"profile_picture": file_url}}
            )

        return redirect('profile')
    else:
        return redirect('profile')
def get_friends(user):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    user_collection = db[USER_COLLECTION]
    friends_usernames = user.get('friends', [])
    return list(user_collection.find({'username': {'$in': friends_usernames}}))
def save_post_to_mongo(username, post_content, file_urls):
    post = {
        'username': username,
        'content': post_content,
        'file_urls': file_urls,
        'created_at': datetime.now(),
        'likes': 0,
        'liked_by': [],
        'comments': [],
        'comment_count': 0
    }
    result = db['posts'].insert_one(post)
    return result.inserted_id is not None
def add_post(request):
    if request.method == 'POST':
        post_content = request.POST.get('post_content')
        username = request.session.get('username')
        file_urls = []
        user_collection = db[USER_COLLECTION]
        current_user = user_collection.find_one({'username': username})
        profile_picture = current_user.get('profile_picture', 'default.png') if current_user else 'default.png'
        if 'post_files' in request.FILES:
            files = request.FILES.getlist('post_files')
            fs = FileSystemStorage()

            for file in files:
                filename = fs.save(file.name, file)
                file_url = fs.url(filename)

                full_file_url = request.build_absolute_uri(file_url)
                file_urls.append(full_file_url)

        post_saved = save_post_to_mongo(username, post_content, file_urls)

        if post_saved:
            return JsonResponse({'success': True, 'username': username, 'post_content': post_content, 'file_urls': file_urls, 'likes': 0,'profile_picture': profile_picture,'comment_count':0})
        else:
            return JsonResponse({'success': False, 'error_message': 'Post kaydedilemedi.'})

    return JsonResponse({'success': False, 'error_message': 'Geçersiz istek.'})
@csrf_exempt
def add_story(request):
    if request.method == 'POST':
        files = request.FILES.getlist('story_files')

        username = request.user.username if request.user.is_authenticated else request.session.get('username', 'guest')

        if username == 'guest':
            return JsonResponse({'success': False, 'error': 'Kullanıcı oturumu bulunamadı.'})

        story_folder = os.path.join(settings.MEDIA_ROOT, 'stories')
        os.makedirs(story_folder, exist_ok=True)

        file_urls = []
        for file in files:
            original_filename = file.name
            file_extension = os.path.splitext(original_filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            file_path = os.path.join(story_folder, unique_filename)

            with open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            file_url = f'{settings.MEDIA_URL}stories/{unique_filename}'
            file_urls.append(file_url)

        existing_story = db['stories'].find_one({'username': username})
        if existing_story:
            db['stories'].update_one(
                {'username': username},
                {'$addToSet': {'file_url': {'$each': file_urls}}}
            )
        else:
            db['stories'].insert_one({'username': username, 'file_url': file_urls})

        return JsonResponse({'success': True, 'stories': [{'file_url': url} for url in file_urls]})

    return JsonResponse({'success': False, 'error': 'Geçersiz istek'})
@csrf_exempt
def get_stories(request):
    try:
        user_collection = db[USER_COLLECTION]

        stories = list(story_collection.find({}, {'_id': 0}))
        username = request.session.get('username')
        user = user_collection.find_one({"username": username})
        grouped_stories = {}
        for story in stories:
            username = story.get('username', 'unknown')
            file_urls = story.get('file_url', [])

            if username not in grouped_stories:
                grouped_stories[username] = []

            grouped_stories[username].extend(file_urls)

        result = [{'username': username, 'file_urls': file_urls} for username, file_urls in grouped_stories.items()]

        return JsonResponse({'success': True, 'stories': result,

                             })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
def save_story_to_mongo(username, file_urls):
    story_collection = db[STORY_COLLECTION]

    try:
        story = {
            'username': username,
            'file_urls': file_urls,
            'created_at': datetime.now()
        }
        story_collection.insert_one(story)
        return True
    except Exception as e:
        print(f"Hata: {e}")
        return False
def add_comment(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        post_id = data.get('post_id')
        comment_content = data.get('comment_content')
        commenter = request.session.get('username')

        if post_id and comment_content:

            db['posts'].update_one(
                {'_id': ObjectId(post_id)},
                {
                    '$push': {'comments': {'commenter': commenter, 'content': comment_content, 'created_at': datetime.now()}},
                    '$inc': {'comment_count': 1}
                }
            )
            return JsonResponse({'success': True, 'comment_content': comment_content, 'commenter': commenter})
        return JsonResponse({'success': False, 'error_message': 'Comment could not be saved.'})

    return JsonResponse({'success': False, 'error_message': 'Invalid request.'})
def like_post(request):
    if request.method == 'POST':
        post_id = request.POST.get('post_id')
        username = request.session.get('username')

        if not username:
            return JsonResponse({'success': False, 'error_message': 'You need to be logged in to like posts.'})

        post = db['posts'].find_one({'_id': ObjectId(post_id)})

        if post:
            if username in post.get('liked_by', []):
                db['posts'].update_one(
                    {'_id': ObjectId(post_id)},
                    {'$inc': {'likes': -1}, '$pull': {'liked_by': username}}
                )
                return JsonResponse({'success': True, 'likes': post['likes'] - 1, 'liked': False})
            else:
                db['posts'].update_one(
                    {'_id': ObjectId(post_id)},
                    {'$inc': {'likes': 1}, '$push': {'liked_by': username}}
                )
                return JsonResponse({'success': True, 'likes': post['likes'] + 1, 'liked': True})

        return JsonResponse({'success': False, 'error_message': 'Post not found.'})

    return JsonResponse({'success': False, 'error_message': 'Invalid request.'})
def logout(request):
    auth_logout(request)
    return redirect('/')
def profile_view(request):
    username = request.session.get('username')
    if username:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        user_collection = db[USER_COLLECTION]
        post_collection = db[POST_COLLECTION]
        group_collection = db[GROUP_COLLECTION]
        topic_collection = db[TOPIC_COLLECTION]
        topic_comment_collection = db[TOPIC_COMMENT_COLLECTION]
        comment_collection = db[COMMENT_COLLECTION]
        join_request_collection = db[JOIN_REQUEST_COLLECTION]
        friend_request_collection = db[FRIEND_REQUEST_COLLECTION]
        messages_collection = db['messages']
        membership_request_collection = db['membership_requests']
        user = user_collection.find_one({"username": username})
        pp = user_collection.find_one({"profile_picture": user['profile_picture']})
        current_user = user_collection.find_one({'username': username})
        story_collection = db[STORY_COLLECTION]

        profile_picture = current_user.get('profile_picture', 'default.png') if current_user else 'default.png'
        if not user:
            error_message = "Kullanıcı bulunamadı."
            return render(request, 'profile.html', {'error_message': error_message})
        groups = group_collection.find()
        posts = post_collection.find().sort("created_at", -1)
        requests = list(friend_request_collection.find({'to_user': username, 'status': 'pending'}))
        friends = get_friends(user)
        reqqq = friend_request_collection.find_one({}, {"_id": 1})
        if reqqq:
            reqqq = str(reqqq['_id'])
        if request.method == 'POST':
            new_username = request.POST.get('new_username')
            if new_username:
                if user_collection.find_one({"username": new_username}):
                    messages.error(request, 'Bu isim zaten alınmış.')
                    return redirect('/profile')
                user_collection.update_one({'_id': user['_id']}, {'$set': {'username': new_username}})
                user_collection.update_one(
                    {'_id': user['_id']},
                    {'$set': {
                        'friends': [new_username if friend == username else friend for friend in user['friends']]}}
                )
                post_collection.update_many({'username': username}, {'$set': {'username': new_username}})
                story_collection.update_many({'username':username}, {'$set': {'username': new_username}})
                group_collection.update_many({'owner': username}, {'$set': {'owner': new_username}})
                topic_collection.update_many({'username': username}, {'$set': {'username': new_username}})
                topic_comment_collection.update_many({'author': username}, {'$set': {'author': new_username}})
                comment_collection.update_many({'author': username}, {'$set': {'author': new_username}})
                join_request_collection.update_many({'username': username}, {'$set': {'username': new_username}})
                friend_request_collection.update_many({'from_user': username}, {'$set': {'from_user': new_username}})
                friend_request_collection.update_many({'to_user': username}, {'$set': {'to_user': new_username}})
                messages_collection.update_many({'sender': username}, {'$set': {'sender': new_username}})
                messages_collection.update_many({'recipient': username}, {'$set': {'recipient': new_username}})
                membership_request_collection.update_many({'username': username}, {'$set': {'username': new_username}})
                user_collection.update_many(
                    {'friends': username},
                    {'$set': {'friends.$': new_username}}
                )
                request.session['username'] = new_username
                messages.success(request, 'İsim başarıyla değiştirildi.')
                return redirect('/profile')
            else:
                messages.error(request, 'Geçersiz isim!')
        username = request.session.get('username')
        context = get_common_context(username, db)
        context.update({
            'email': user['email'],
            'profile_picture': profile_picture,
            'pp': pp,
            'username': user['username'],
            'requests': requests,
            'reqqq': reqqq,
            'friends': friends,
            'groups': groups,
            'posts': posts,
        })

        return render(request, 'profile.html', context)
    else:
        return redirect('/login')
@csrf_exempt
def delete_account(request):
    if request.method == 'POST':
        username = request.session.get('username')

        if username:
            client = MongoClient(MONGO_URI)
            db = client[DATABASE_NAME]

            user_collection = db[USER_COLLECTION]
            post_collection = db[POST_COLLECTION]
            group_collection = db[GROUP_COLLECTION]
            topic_collection = db[TOPIC_COLLECTION]
            comment_collection = db[COMMENT_COLLECTION]
            join_request_collection = db[JOIN_REQUEST_COLLECTION]
            friend_request_collection = db[FRIEND_REQUEST_COLLECTION]
            messages_collection = db['messages']
            membership_request_collection = db[MEMBERSHIP_REQUEST_COLLECTION]

            user_collection.delete_one({"username": username})

            post_collection.delete_many({"username": username})

            group_collection.delete_many({"owner": username})

            topic_collection.delete_many({"username": username})
            comment_collection.delete_many({"username": username})
            comment_collection.delete_many({"replied_to": username})

            join_request_collection.delete_many({"username": username})
            friend_request_collection.delete_many({"from_user": username})
            friend_request_collection.delete_many({"to_user": username})
            membership_request_collection.delete_many({"username": username})

            messages_collection.delete_many({"from_user": username})
            messages_collection.delete_many({"to_user": username})

            request.session.flush()

            return JsonResponse({"status": "success"}, status=200)
        else:
            return JsonResponse({"error": "User not found"}, status=404)

    return JsonResponse({"error": "Invalid request"}, status=400)
@csrf_exempt
def delete_post(request):
    if request.method == 'POST':
        post_data = json.loads(request.body)
        post_id = post_data.get('post_id')

        if post_id:
            try:
                client = MongoClient(MONGO_URI)
                db = client[DATABASE_NAME]
                post_collection = db[POST_COLLECTION]

                result = post_collection.delete_one({"_id": ObjectId(post_id)})

                if result.deleted_count == 1:
                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'success': False, 'message': 'Post bulunamadı.'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': str(e)})
        else:
            return JsonResponse({'success': False, 'message': 'Post ID alınamadı.'})
    return JsonResponse({'success': False, 'message': 'Geçersiz istek.'})
@csrf_exempt
def remove_friend(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = request.session.get('username')
            friend_username = data.get('friend_username')

            if username and friend_username:
                client = MongoClient(MONGO_URI)
                db = client[DATABASE_NAME]
                user_collection = db[USER_COLLECTION]
                friend_request_collection = db[FRIEND_REQUEST_COLLECTION]

                user = user_collection.find_one({"username": username})
                friend = user_collection.find_one({"username": friend_username})

                if user and friend:
                    user_collection.update_one(
                        {"username": username},
                        {"$pull": {"friends": friend_username}}
                    )
                    user_collection.update_one(
                        {"username": friend_username},
                        {"$pull": {"friends": username}}
                    )

                    friend_request_collection.delete_one({
                        "$or": [
                            {"from_user": username, "to_user": friend_username},
                            {"from_user": friend_username, "to_user": username}
                        ]
                    })

                    return JsonResponse({"message": "Arkadaş başarıyla çıkarıldı."})
                else:
                    return JsonResponse({"error": "Kullanıcı bulunamadı."}, status=404)
            else:
                return JsonResponse({"error": "Geçersiz istek."}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Geçersiz JSON formatı."}, status=400)
    else:
        return JsonResponse({"error": "Geçersiz metod."}, status=405)
def send_friend_request(request, username):
    if request.method == 'POST':
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        friend_request_collection = db[FRIEND_REQUEST_COLLECTION]

        friend_request = {
            'from_user': request.session.get('username'),
            'to_user': username,
            'status': 'pending'
        }

        friend_request_collection.insert_one(friend_request)

        return redirect('profile')

    return redirect('profile')
def accept_friend_request(request, request_id):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    friend_request_collection = db[FRIEND_REQUEST_COLLECTION]
    user_collection = db[USER_COLLECTION]

    try:
        friend_request_id = ObjectId(request_id)
    except Exception as e:
        print(f"Invalid ObjectId: {request_id} - {e}")
        return redirect('profile')

    friend_request = friend_request_collection.find_one({'_id': friend_request_id})

    if friend_request:
        from_user = friend_request['from_user']
        to_user = friend_request['to_user']

        friend_request_collection.update_one(
            {'_id': friend_request_id},
            {'$set': {'status': 'accepted'}}
        )

        user_collection.update_one(
            {'username': from_user},
            {'$addToSet': {'friends': to_user}}
        )
        user_collection.update_one(
            {'username': to_user},
            {'$addToSet': {'friends': from_user}}
        )

        return redirect('profile')

    return redirect('profile')
def reject_friend_request(request, request_id):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    friend_request_collection = db[FRIEND_REQUEST_COLLECTION]

    friend_request = friend_request_collection.find_one({'_id': ObjectId(request_id)})

    if friend_request and friend_request['status'] == 'pending':
        friend_request_collection.update_one(
            {'_id': ObjectId(request_id)},
            {'$set': {'status': 'rejected'}}
        )

    return redirect('profile')
def search_friends(request):
    if request.method == 'POST':
        search_query = request.POST.get('search_query')
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        collection = db[USER_COLLECTION]
        user_collection = db[USER_COLLECTION]
        group_collection = db['groups']
        friend_request_collection = db[FRIEND_REQUEST_COLLECTION]
        groups = list(group_collection.find())
        usernamea = request.session.get('username')
        username = request.session.get('username')
        user = user_collection.find_one({"username": usernamea})
        friens = [friend['username'] for friend in get_friends(user)]
        friends = get_friends(user)
        post_collection = db[POST_COLLECTION]
        requests = list(friend_request_collection.find({'to_user': username, 'status': 'pending'}))
        posts = post_collection.find().sort("created_at", -1)

        posts_with_pictures = []
        for post in posts:
            post['_id'] = str(post['_id'])
            post_user = user_collection.find_one({'username': post['username']})
            post['profile_picture'] = post_user.get('profile_picture', 'default.png') if post_user else 'default.png'
            posts_with_pictures.append(post)
        results = list(collection.find({"username": {"$regex": search_query, "$options": "i"}}))

        for result in results:
            reqqq = friend_request_collection.find_one(
                {
                    "$or": [
                        {"from_user": usernamea, "to_user": result['username']},
                        {"from_user": result['username'], "to_user": usernamea}
                    ]
                },
                {"status": 1},
                sort=[("_id", DESCENDING)]
            )
            result['friend_request_status'] = reqqq
            username = request.session.get('username')
            pp = user_collection.find_one({"profile_picture": user['profile_picture']})
            current_user = user_collection.find_one({'username': username})
            profile_picture = current_user.get('profile_picture', 'default.png') if current_user else 'default.png'
        context = get_common_context(username, db)
        context.update({
            'search_results': results,
            'search_query': search_query,
            'username': usernamea,
            'friens': friens,
            'friends': friends,
            'user': user,
            'groups': groups,
            'email': user['email'],
            'requests': requests,
        })
        return render(request, 'profile.html', context)

    return redirect('profile')
def add_group(request):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    group_collection = db[GROUP_COLLECTION]

    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        username = request.session.get('username')
        members = request.POST.getlist('members')

        if not group_name or not username:
            return render(request, 'add_group.html', {'error_message': 'Grup adı veya kullanıcı bilgisi eksik.'})

        existing_group = group_collection.find_one({'name': group_name})
        if existing_group:
            groups = group_collection.find()
            group_list = [{'id': str(group['_id']), 'name': group['name']} for group in groups]
            return render(request,  'add_group.html',{
                'error_message': f'"{group_name}" adında bir grup zaten var.',
                'groups': group_list
            })

        new_group = {
            'name': group_name,
            'owner': username,
            'members': members
        }
        group_collection.insert_one(new_group)
        return redirect('add_group')

    groups = group_collection.find()
    group_list = [{'id': str(group['_id']), 'name': group['name']} for group in groups]
    username = request.session.get('username')
    context = get_common_context(username, db)
    context.update({
        'groups': group_list
    })
    return render(request, 'add_group.html', context)
def group_detail(request, group_id):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    group_collection = db[GROUP_COLLECTION]
    group = group_collection.find_one({'_id': ObjectId(group_id)})
    req_col = db[MEMBERSHIP_REQUEST_COLLECTION]
    username = request.session.get('username')
    req = req_col.find_one({'group_id': group_id, 'status': 'pending', 'username': username})

    group_id_str = str(group['_id'])

    user_username = username if username else 'Guest'
    context = get_common_context(username, db)
    context.update({
        'group': {
            'id': group_id_str,
            'name': group['name'],
            'owner': group['owner'],
            'members': group.get('members', [])
        },
        'group_id_str': group_id_str,
        'user_username': user_username,
        'req_col': req,
        'is_group_detail': True
    })
    return render(request, 'group_detail.html', context)

events_collection = db['events']
def create_event(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            event_name = data.get('event_name')
            event_duration = int(data.get('event_duration'))
            group_id = data.get('group_id')

            user_username = request.session.get('username')

            if not user_username:
                return JsonResponse({"success": False, "error": "Kullanıcı bilgisi bulunamadı."})

            utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)

            tz = pytz.timezone('Europe/Istanbul')

            current_time = utc_now.astimezone(tz)

            start_time = current_time - timedelta(hours=-3)

            end_time = start_time + timedelta(hours=event_duration)

            events_collection.insert_one({
                "event_name": event_name,
                "event_duration": event_duration,
                "start_time": start_time,
                "end_time": end_time,
                "group_id": group_id,
                "created_by": user_username,
                "created_at": utc_now
            })

            return JsonResponse({
                "success": True,
                "message": f"{event_name} etkinliği {user_username} tarafından oluşturuldu.",
                "start_time": start_time.strftime('%Y-%m-%d %H:%M'),
                "end_time": end_time.strftime('%Y-%m-%d %H:%M')
            })

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Geçersiz istek!"})
def get_events(request):
    group_id = request.GET.get('group_id')
    if group_id:
        utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
        events_collection.delete_many({"end_time": {"$lt": utc_now}})

        events = events_collection.find({"group_id": group_id})

        event_list = []
        for event in events:
            start_time_local = None
            end_time_local = None

            if "start_time" in event:
                tz = pytz.timezone('Europe/Istanbul')
                start_time_local = event["start_time"].astimezone(tz)

            if "end_time" in event:
                end_time_local = event["end_time"].astimezone(tz)

            event_list.append({
                "event_name": event.get("event_name", "Etkinlik adı yok"),
                "start_time": start_time_local.strftime('%Y-%m-%d %H:%M') if start_time_local else "Bilinmiyor",
                "end_time": end_time_local.strftime('%Y-%m-%d %H:%M') if end_time_local else "Bilinmiyor",
                "created_by": event.get("created_by", "Bilinmiyor")
            })

        return JsonResponse({"events": event_list}, status=200)

    return JsonResponse({"error": "Geçersiz grup kimliği"}, status=400)
def request_membership(request, group_id):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    request_collection = db['membership_requests']

    if request.method == 'POST':
        username = request.session.get('username')
        if username:
            membership_request = {
                'group_id': group_id,
                'username': username,
                'status': 'pending'
            }
            request_collection.insert_one(membership_request)
            return redirect('group_detail', group_id=group_id)

    return redirect('group_detail', group_id=group_id)
def manage_requests(request, group_id):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    membership_requests_collection = db['membership_requests']
    group_collection = db[GROUP_COLLECTION]

    group = group_collection.find_one({'_id': ObjectId(group_id)})

    if not group or group['owner'] != request.session.get('username'):
        return redirect('group_detail', group_id=group_id)

    pending_requests = membership_requests_collection.find({'group_id': group_id, 'status': 'pending'})

    pending_requests_list = [
        {**req, 'id_str': str(req['_id'])} for req in pending_requests
    ]

    return render(request, 'manage_requests.html', {
        'group': group,
        'pending_requests': pending_requests_list
    })
def approve_request(request, request_id):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    membership_requests_collection = db['membership_requests']
    group_collection = db[GROUP_COLLECTION]

    membership_request = membership_requests_collection.find_one({'_id': ObjectId(request_id)})

    if membership_request and membership_request['status'] == 'pending':
        group_id = membership_request['group_id']
        group = group_collection.find_one({'_id': ObjectId(group_id)})

        if group and group['owner'] == request.session.get('username'):
            group_collection.update_one(
                {'_id': ObjectId(group_id)},
                {'$addToSet': {'members': membership_request['username']}}
            )
            membership_requests_collection.update_one(
                {'_id': ObjectId(request_id)},
                {'$set': {'status': 'approved'}}
            )

    return redirect('manage_requests', group_id=membership_request['group_id'])
def reject_request(request, request_id):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    membership_requests_collection = db['membership_requests']

    membership_request = membership_requests_collection.find_one({'_id': ObjectId(request_id)})

    if membership_request and membership_request['status'] == 'pending':
        group_id = membership_request['group_id']
        group = db[GROUP_COLLECTION].find_one({'_id': ObjectId(group_id)})

        if group and group['owner'] == request.session.get('username'):
            membership_requests_collection.update_one(
                {'_id': ObjectId(request_id)},
                {'$set': {'status': 'rejected'}}
            )

    return redirect('manage_requests', group_id=membership_request['group_id'])
def leave_group(request, group_id):
    if request.method == 'POST':
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        group_collection = db[GROUP_COLLECTION]

        username = request.session.get('username')
        group = group_collection.find_one({'_id': ObjectId(group_id)})

        if not group:
            return JsonResponse({'error': 'Grup bulunamadı.'}, status=404)

        if username in group['members']:
            group_collection.update_one(
                {'_id': ObjectId(group_id)},
                {'$pull': {'members': username}}
            )
            return JsonResponse({'message': 'Gruptan başarıyla ayrıldınız.'})
        else:
            return JsonResponse({'error': 'Kullanıcı grupta değil.'}, status=400)
    return JsonResponse({'error': 'Geçersiz istek.'}, status=405)
def remove_member(request, group_id):
    if request.method == "POST":
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        group_collection = db[GROUP_COLLECTION]

        group = group_collection.find_one({'_id': ObjectId(group_id)})
        if not group:
            return JsonResponse({'error': 'Grup bulunamadı.'}, status=404)

        username = request.POST.get('username')
        current_user = request.session.get('username')

        if group['owner'] != current_user:
            return JsonResponse({'error': 'Yalnızca grup sahibi üye çıkarabilir.'}, status=403)

        if username == group['owner']:
            return JsonResponse({'error': 'Grup sahibi gruptan çıkarılamaz.'}, status=400)

        if username in group['members']:
            group_collection.update_one(
                {'_id': ObjectId(group_id)},
                {'$pull': {'members': username}}
            )
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'Bu üye grupta bulunmuyor.'}, status=404)

    return JsonResponse({'error': 'Geçersiz istek.'}, status=400)
def get_membership_requests(request, group_id):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    request_collection = db['membership_requests']

    pending_requests = list(request_collection.find({'group_id': group_id, 'status': 'pending'}))

    requests_data = []
    for req in pending_requests:
        requests_data.append({
            'id': str(req['_id']),
            'username': req['username'],
        })

    return JsonResponse({'pending_requests': requests_data})
def check_new_messages(request):
    user = request.session.get('username')
    if user:
        try:
            new_messages = db.messages.count_documents({"recipient": user, "read": False}) > 0
            return JsonResponse({'new_message': new_messages})
        except Exception as e:
            return JsonResponse({'new_message': False, 'error': str(e)}, status=500)
    return JsonResponse({'new_message': False}, status=401)
@csrf_exempt
def mark_messages_as_read_view(request, sender, recipient):
    if request.method == "POST":
        updated_count = mark_messages_as_read(sender, recipient)
        if updated_count > 0:
            return JsonResponse({'status': 'success', 'updated': updated_count})
        else:
            return JsonResponse({'status': 'no_updates'}, status=404)
    return JsonResponse({'status': 'error'}, status=400)
def mark_messages_as_read(sender, recipient):

    result = messages_collection.update_many(
        {"sender": recipient, "recipient": sender, "read": False},
        {"$set": {"read": True}}
    )
    return result.modified_count
@csrf_exempt
def send_message(request):
    if request.method == 'POST':
        try:
            message_data = json.loads(request.POST.get('message_data', '{}'))
            message_content = message_data.get('message')
            recipient = message_data.get('recipient')
            sender = message_data.get('sender')

            file = request.FILES.get('file')
            file_name = file.name if file else None
            file_size = file.size if file else None
            file_data = file.read() if file else None

            if not recipient or not sender or (not message_content and not file):
                return JsonResponse({'success': False, 'error': 'Eksik veri'}, status=400)

            message = {
                'sender': sender,
                'recipient': recipient,
                'text': message_content,
                'file_name': file_name,
                'file_size': file_size,
                'file_data': file_data,
                'timestamp': timezone.now(),
                'read': False
            }
            messages_collection.insert_one(message)

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{recipient}',
                {
                    'type': 'chat_message',
                    'message': message_content,
                    'sender': sender,
                    'recipient': recipient,
                    'file_name': file_name,
                    'file_size': file_size,
                    'file_data': base64.b64encode(file_data).decode('utf-8') if file_data else None,
                    'notification': 'new_message'
                }
            )

            return JsonResponse({'success': True})

        except Exception as e:
            print(f"Hata (send_message): {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False}, status=400)
def fetch_messages(request):
    try:
        friend = request.GET.get('friend')
        last_timestamp_str = request.GET.get('last_timestamp')

        if not friend:
            return JsonResponse({'success': False, 'error': 'Arkadaş parametresi gerekli'}, status=400)

        user = request.session.get('username')
        if not user:
            return JsonResponse({'success': False, 'error': 'Kullanıcı doğrulanmadı'}, status=400)

        last_timestamp = None
        if last_timestamp_str:
            try:
                last_timestamp = datetime.fromisoformat(last_timestamp_str)
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Geçersiz zaman formatı'}, status=400)

        query = {
            '$or': [
                {'sender': user, 'recipient': friend},
                {'sender': friend, 'recipient': user}
            ]
        }
        if last_timestamp:
            query['timestamp'] = {'$gt': last_timestamp}

        messages = list(messages_collection.find(query).sort('timestamp', 1))

        formatted_messages = []
        for msg in messages:
            formatted_message = {
                'sender': msg['sender'],
                'recipient': msg['recipient'],
                'text': msg.get('text', ''),
                'file_name': msg.get('file_name'),
                'file_size': msg.get('file_size'),
                'file_type': msg.get('file_type'),
                'timestamp': msg['timestamp'].isoformat() if 'timestamp' in msg else datetime.utcnow().isoformat()
            }

            file_data = msg.get('file_data')
            if file_data:
                if isinstance(file_data, bytes):
                    formatted_message['file_data'] = base64.b64encode(file_data).decode('utf-8')
                else:
                    formatted_message['file_data'] = file_data

            formatted_messages.append(formatted_message)

        return JsonResponse({'messages': formatted_messages})

    except Exception as e:
        print(f"Error (fetch_messages): {e}")
        return JsonResponse({'success': False, 'error': f'Sunucu hatası: {str(e)}'}, status=500)
@database_sync_to_async
def save_message(sender, recipient, message, file_name=None, file_size=None, file_data=None):

    if file_data:
        try:
            file_data = base64.b64decode(file_data)
            print("Decoded File Data Length:", len(file_data))
        except Exception as e:
            print("Error decoding file data:", e)
            file_data = None

    message_data = {
        'sender': sender,
        'recipient': recipient,
        'text': message,
        'file_name': file_name,
        'file_size': file_size,
        'file_data': file_data,
        'timestamp': timezone.now()
    }

    try:
        result = messages_collection.insert_one(message_data)
        print("Message Inserted with ID:", result.inserted_id)
    except Exception as e:
        print("Error inserting message:", e)
@csrf_exempt
def fetch_group_messages(request):
    group_id = request.GET.get('group_id')
    last_timestamp = request.GET.get('last_timestamp')

    query = {'group_id': group_id}

    if last_timestamp and last_timestamp != 'null':
        query['timestamp'] = {'$gt': last_timestamp}

    start_time = time.time()
    timeout_duration = 10

    while True:
        messages = list(messages_collection.find(query).sort('timestamp', 1))

        if messages:
            formatted_messages = [
                {'sender': msg['sender'], 'text': msg['text'], 'timestamp': msg['timestamp']}
                for msg in messages
            ]
            return JsonResponse({'messages': formatted_messages})

        if time.time() - start_time > timeout_duration:
            return JsonResponse({'messages': []})

        time.sleep(1)
@csrf_exempt
def send_group_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        group_id = data.get('group_id')
        text = data.get('text')
        user = request.session.get('username')

        if user:
            messages_collection.insert_one({
                'group_id': group_id,
                'sender': user,
                'text': text,
                'timestamp': datetime.now()
            })
            return JsonResponse({'status': 'success'})

        return JsonResponse({'status': 'error', 'message': 'User not authenticated.'}, status=401)