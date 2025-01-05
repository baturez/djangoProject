import base64
from django.core.mail import EmailMessage
from datetime import datetime,timedelta
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
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
import hashlib
import uuid

MONGO_URI = 'mongodb+srv://batuhanfahri06:PezQB4OKaTHSEjFm@bartini.qyrro.mongodb.net/?retryWrites=true&w=majority&appName=bartini'
DATABASE_NAME = 'my_database'
USER_COLLECTION = 'users'
POST_COLLECTION = 'posts'
GROUP_COLLECTION = 'groups'
TOPIC_COLLECTION = 'topics'
TOPIC_COMMENT_COLLECTION = 'topic_comments'
COMMENT_COLLECTION = 'comments'
JOIN_REQUEST_COLLECTION = 'join_request'
FRIEND_REQUEST_COLLECTION = 'friend_requests'
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
messages_collection = db['messages']
notifications_collection = db['notifications']
MEMBERSHIP_REQUEST_COLLECTION = 'membership_requests'

def index(request):
    return render(request, "index.html")
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
        post['_id'] = str(post['_id'])  # Convert _id to string for template usage

        # Add the profile picture to the post
        post_user = db[USER_COLLECTION].find_one({'username': post.get('username')})
        post['profile_picture'] = post_user.get('profile_picture', 'default.png') if post_user else 'default.png'
        context = get_common_context(username, db)
        context.update({
            'post': post,
            'popular_posts': popular_posts
        })
        if 'comments' in post:
            for comment in post['comments']:
                comment['created_at'] = comment.get('created_at', 'Unknown')

        return render(request, 'post_view.html', context)
    else:
        return render(request, 'post_view.html', {'error': 'Post not found.'})
def home(request):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]

    username = request.session.get('username')  # Oturumdaki kullanıcı adı
    user_collection = db[USER_COLLECTION]
    post_collection = db[POST_COLLECTION]
    group_collection = db[GROUP_COLLECTION]

    # Mevcut kullanıcı bilgisi
    current_user = user_collection.find_one({'username': username})
    friends = get_friends(current_user) if current_user else []
    profile_picture = current_user.get('profile_picture', 'default.png') if current_user else 'default.png'

    # Gönderileri çekme ve her gönderi için profil fotoğrafını bulma
    posts = post_collection.find().sort("created_at", -1)
    posts_with_pictures = []
    for post in posts:
        post['_id'] = str(post['_id'])  # MongoDB _id'yi stringe çevir
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

    # Mevcut kullanıcı bilgisi
    current_user = user_collection.find_one({'username': username})
    friends = get_friends(current_user) if current_user else []
    profile_picture = current_user.get('profile_picture', 'default.png') if current_user else 'default.png'

    # Gönderiler ve profil fotoğrafları
    posts = post_collection.find().sort("created_at", -1)
    posts_with_pictures = []
    for post in posts:
        post['_id'] = str(post['_id'])  # MongoDB _id'yi stringe çevir
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

    return {
        'posts': posts_with_pictures,
        'groups': groups,
        'current_user': current_user,
        'friends': friends,
        'topics': topics,
        'popular_posts': popular_posts,
        'profile_picture': profile_picture,
        'username': username,
    }
def topic(request):
    username = request.session.get('username')
    context = get_common_context(username, db)
    context.update({

    })
    return render(request, "topics.html" ,context)
def get_topics(request):
    if request.method == 'GET':
        try:
            topics = list(db[TOPIC_COLLECTION].find())

            if not topics:
                return JsonResponse({'error': 'No topics found.'}, status=404)

            # Konuları düzenle
            for topic in topics:
                topic['_id'] = str(topic['_id'])
                topic['likes_count'] = topic.get('like', 0)  # Integer değer al
                topic['dislikes_count'] = topic.get('dislike', 0)  # Integer değer al

            return JsonResponse({'topics': topics}, safe=False)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
def list_topics(request):
    topics = db[TOPIC_COLLECTION].find().sort('like', -1).limit(3)  # Like'a göre azalan sırala ve ilk 3 konuyu al
    for topic in topics:
        topic['_id'] = str(topic['_id'])  # JSON uyumu için ID'yi stringe çevir
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
                'like': 0,  # Integer olarak başlatıyoruz
                'dislike': 0  # Integer olarak başlatıyoruz
            }

            result = db[TOPIC_COLLECTION].insert_one(new_topic)
            topic_id = str(result.inserted_id)

            return JsonResponse({
                'success': True,
                'message': 'Topic created successfully!',
                'topic_id': topic_id,
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

            # Yeni yorum oluştur
            new_comment = {
                'topic_id': ObjectId(topic_id),
                'comment_text': comment_text,
                'created_at': datetime.now(),
                'commenter': commenter
            }

            # MongoDB'ye yeni yorumu ekle
            db['topic_comments'].insert_one(new_comment)

            # Konunun comment_count'ını artır
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
                return JsonResponse({'success': False, 'error_message': 'You have already liked this topic.'}, status=400)

            if user_likes.get(username) == 'disliked':
                return JsonResponse({'success': False, 'error_message': 'You have already disliked this topic. Please remove your dislike before liking.'}, status=400)

            # Increment likes
            likes = topic.get('like', 0)
            likes += 1

            user_likes[username] = 'liked'

            db[TOPIC_COLLECTION].update_one(
                {'_id': ObjectId(topic_id)},
                {'$set': {'like': likes, 'user_likes': user_likes}}
            )

            return JsonResponse({'success': True, 'message': 'Topic liked successfully!'}, status=200)

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
                return JsonResponse({'success': False, 'error_message': 'You have already disliked this topic.'}, status=400)

            if user_likes.get(username) == 'liked':
                return JsonResponse({'success': False, 'error_message': 'You have already liked this topic. Please remove your like before disliking.'}, status=400)

            # Increment dislikes
            dislikes = topic.get('dislike', 0)
            dislikes += 1

            user_likes[username] = 'disliked'

            db[TOPIC_COLLECTION].update_one(
                {'_id': ObjectId(topic_id)},
                {'$set': {'dislike': dislikes, 'user_likes': user_likes}}
            )

            return JsonResponse({'success': True, 'message': 'Topic disliked successfully!'}, status=200)

        except Exception as e:
            return JsonResponse({'success': False, 'error_message': str(e)}, status=400)
def verify_email(request, token):
    user_collection = db[USER_COLLECTION]
    user = user_collection.find_one({"verification_token": token})

    if user:
        # Kullanıcıyı doğrulama başarılı
        user_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"is_verified": True}},
        )
        success_message = "Hesabınız başarıyla doğrulandı!"
        return render(request, 'sign_up.html', {'success_message': success_message})
    else:
        error_message = "Geçersiz doğrulama bağlantısı!"
        return render(request, 'sign_up.html', {'error_message': error_message})


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

        # Yeni kayıt yapılıyor
        if save_to_mongo(email, username, password):
            success_message = "Kayıt işlemi başarılı! Lütfen e-posta adresinizi doğrulayın."

            # Yeni benzersiz token oluşturuluyor
            token = str(uuid.uuid4())  # Benzersiz token
            user_collection.update_one(
                {"email": email},
                {"$set": {"verification_token": token}}
            )

            verification_link = f"http://bartini.online/verify/{token}"

            subject = "E-posta Doğrulaması"

            # HTML şablonunu render et
            message = render_to_string('email/verify_email.html', {
                'username': username,
                'verification_link': verification_link,
            })

            # HTML e-posta gönderme
            email_message = EmailMessage(
                subject,
                message,
                'no-reply@bartini.com',
                [email]
            )
            email_message.content_subtype = "html"  # HTML formatında göndermek için
            email_message.send()

            return render(request, 'sign_up.html', {'success_message': success_message})
        else:
            error_message = "Kayıt işlemi sırasında bir hata oluştu."
            return render(request, 'sign_up.html', {'error_message': error_message})

    return render(request, 'sign_up.html')
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password').encode('utf-8')

        try:
            client = MongoClient(MONGO_URI)
            db = client[DATABASE_NAME]
            collection = db[USER_COLLECTION]

            user = collection.find_one({"username": username})

            if user and bcrypt.checkpw(password, user['password']):
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
def save_to_mongo(email, username, password):
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
            "profile_picture": default_profile_picture
        }

        result = collection.insert_one(user_data)
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

        # Save the image to the media directory using Django's FileSystemStorage
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        filename = fs.save(profile_picture.name, profile_picture)
        file_url = filename  # Save only the relative path

        # Get the logged-in user
        username = request.session.get('username')

        if username:
            client = MongoClient(MONGO_URI)
            db = client[DATABASE_NAME]
            user_collection = db[USER_COLLECTION]

            # Update the user's profile_picture field in MongoDB
            user_collection.update_one(
                {"username": username},
                {"$set": {"profile_picture": file_url}}  # Store relative file path, not full URL
            )

        return redirect('profile')  # Redirect to the profile page after upload
    else:
        return redirect('profile')
def get_friends(user):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    user_collection = db[USER_COLLECTION]
    # Kullanıcının arkadaş listesini al
    friends_usernames = user.get('friends', [])
    # Arkadaşların kullanıcı bilgilerini veritabanından al
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
            return JsonResponse({'success': True, 'username': username, 'post_content': post_content, 'file_urls': file_urls, 'likes': 0})
        else:
            return JsonResponse({'success': False, 'error_message': 'Post kaydedilemedi.'})

    return JsonResponse({'success': False, 'error_message': 'Geçersiz istek.'})
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

        post = db['posts'].find_one({'_id': ObjectId(post_id)})

        if post:
            if username in post['liked_by']:
                return JsonResponse({'success': False, 'error_message': 'You have already liked this post.'})
            else:
                db['posts'].update_one(
                    {'_id': ObjectId(post_id)},
                    {'$inc': {'likes': 1}, '$push': {'liked_by': username}}
                )
                return JsonResponse({'success': True, 'likes': post['likes'] + 1})

    return JsonResponse({'success': False, 'error_message': 'Invalid request.'})
def logout(request):
    auth_logout(request)
    return redirect('/')
def profile_view(request):
    username = request.session.get('username')

    if username:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]

        # MongoDB collections
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

        # Get user details
        user = user_collection.find_one({"username": username})
        pp = user_collection.find_one({"profile_picture": user['profile_picture']})
        current_user = user_collection.find_one({'username': username})
        profile_picture = current_user.get('profile_picture', 'default.png') if current_user else 'default.png'
        if not user:
            error_message = "Kullanıcı bulunamadı."
            return render(request, 'profile.html', {'error_message': error_message})

        # Get groups, posts, etc.
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
                # Check if the new username already exists
                if user_collection.find_one({"username": new_username}):
                    messages.error(request, 'Bu isim zaten alınmış.')
                    return redirect('/profile')

                # Update username in all relevant collections
                user_collection.update_one({'_id': user['_id']}, {'$set': {'username': new_username}})

                # Update 'friends' in the current user's document
                user_collection.update_one(
                    {'_id': user['_id']},
                    {'$set': {
                        'friends': [new_username if friend == username else friend for friend in user['friends']]}}
                )

                # Update username in posts
                post_collection.update_many({'username': username}, {'$set': {'username': new_username}})

                # Update username in groups
                group_collection.update_many({'owner': username}, {'$set': {'owner': new_username}})

                # Update username in topics
                topic_collection.update_many({'author': username}, {'$set': {'author': new_username}})

                # Update username in topic comments
                topic_comment_collection.update_many({'author': username}, {'$set': {'author': new_username}})

                # Update username in comments
                comment_collection.update_many({'author': username}, {'$set': {'author': new_username}})

                # Update username in join requests
                join_request_collection.update_many({'username': username}, {'$set': {'username': new_username}})

                # Update username in friend requests
                friend_request_collection.update_many({'from_user': username}, {'$set': {'from_user': new_username}})
                friend_request_collection.update_many({'to_user': username}, {'$set': {'to_user': new_username}})

                # Update username in messages
                messages_collection.update_many({'sender': username}, {'$set': {'sender': new_username}})
                messages_collection.update_many({'recipient': username}, {'$set': {'recipient': new_username}})

                # Update username in membership requests
                membership_request_collection.update_many({'username': username}, {'$set': {'username': new_username}})

                # Update 'friends' in all other users' documents
                user_collection.update_many(
                    {'friends': username},
                    {'$set': {'friends.$': new_username}}
                )

                # Update session with the new username
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
        # Get the current user's username from the session
        username = request.session.get('username')

        if username:
            # Connect to MongoDB
            client = MongoClient(MONGO_URI)
            db = client[DATABASE_NAME]

            # Define collections
            user_collection = db[USER_COLLECTION]
            post_collection = db[POST_COLLECTION]
            group_collection = db[GROUP_COLLECTION]
            topic_collection = db[TOPIC_COLLECTION]
            comment_collection = db[COMMENT_COLLECTION]
            join_request_collection = db[JOIN_REQUEST_COLLECTION]
            friend_request_collection = db[FRIEND_REQUEST_COLLECTION]
            messages_collection = db['messages']
            membership_request_collection = db[MEMBERSHIP_REQUEST_COLLECTION]

            # Delete user from the users collection
            user_collection.delete_one({"username": username})

            # Delete posts related to the user
            post_collection.delete_many({"username": username})

            # Delete the user's groups
            group_collection.delete_many({"owner": username})

            # Delete topics, comments, and replies by the user
            topic_collection.delete_many({"username": username})
            comment_collection.delete_many({"username": username})
            comment_collection.delete_many({"replied_to": username})

            # Delete join requests, friend requests, and membership requests
            join_request_collection.delete_many({"username": username})
            friend_request_collection.delete_many({"from_user": username})
            friend_request_collection.delete_many({"to_user": username})
            membership_request_collection.delete_many({"username": username})

            # Delete messages related to the user
            messages_collection.delete_many({"from_user": username})
            messages_collection.delete_many({"to_user": username})

            # End the session after deletion
            request.session.flush()

            return JsonResponse({"status": "success"}, status=200)
        else:
            return JsonResponse({"error": "User not found"}, status=404)

    return JsonResponse({"error": "Invalid request"}, status=400)
@csrf_exempt
def delete_post(request):
    if request.method == 'POST':
        # JSON verisini al
        post_data = json.loads(request.body)
        post_id = post_data.get('post_id')

        if post_id:
            try:
                # MongoDB bağlantısı
                client = MongoClient(MONGO_URI)
                db = client[DATABASE_NAME]
                post_collection = db[POST_COLLECTION]

                # Postu sil
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

                # Kullanıcı ve arkadaşı bul
                user = user_collection.find_one({"username": username})
                friend = user_collection.find_one({"username": friend_username})

                if user and friend:
                    # Arkadaş listelerini güncelle
                    user_collection.update_one(
                        {"username": username},
                        {"$pull": {"friends": friend_username}}
                    )
                    user_collection.update_one(
                        {"username": friend_username},
                        {"$pull": {"friends": username}}
                    )

                    # Arkadaşlık isteğini sil
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
            post['_id'] = str(post['_id'])  # MongoDB _id'yi stringe çevir
            post_user = user_collection.find_one({'username': post['username']})
            post['profile_picture'] = post_user.get('profile_picture', 'default.png') if post_user else 'default.png'
            posts_with_pictures.append(post)
        # Arama sonuçları
        results = list(collection.find({"username": {"$regex": search_query, "$options": "i"}}))

        # Her kullanıcı için friend request durumunu alalım
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
            result['friend_request_status'] = reqqq  # Durumu ekliyoruz
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
            'profile_picture': profile_picture,
            'pp': pp,
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

        # Grup adı benzersizlik kontrolü
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
    req= req_col.find_one({'group_id': group_id, 'status': 'pending' ,'username': username} )

    group_id_str = str(group['_id'])



    user_username = username if username else 'Guest'
    username = request.session.get('username')
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
        'req_col': req
    })
    return render(request, 'group_detail.html', context)
events_collection = db['events']
def create_event(request):
    if request.method == "POST":
        try:
            # JSON verisini al
            data = json.loads(request.body)
            event_name = data.get('event_name')
            event_duration = int(data.get('event_duration'))  # Etkinlik süresi (örneğin 5 saat)
            group_id = data.get('group_id')

            # Kullanıcı bilgilerini session'dan al
            user_username = request.session.get('username')  # Kullanıcının oturumdaki adı

            if not user_username:
                return JsonResponse({"success": False, "error": "Kullanıcı bilgisi bulunamadı."})

            # UTC zamanı al
            utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)

            # Kullanıcı zaman dilimini al (örneğin, "Europe/Istanbul")
            tz = pytz.timezone('Europe/Istanbul')

            # UTC zamanı Istanbul saat dilimine çevir
            current_time = utc_now.astimezone(tz)

            # Başlangıç saati: şu anki zaman - 3 saat
            start_time = current_time - timedelta(hours=-3)

            # Bitiş saati: başlangıç + etkinlik süresi
            end_time = start_time + timedelta(hours=event_duration)

            # Etkinliği MongoDB'ye kaydet
            events_collection.insert_one({
                "event_name": event_name,
                "event_duration": event_duration,
                "start_time": start_time,  # Başlangıç saati (UTC olarak kaydedilecek)
                "end_time": end_time,  # Bitiş saati (UTC olarak kaydedilecek)
                "group_id": group_id,
                "created_by": user_username,
                "created_at": utc_now  # Etkinlik oluşturulma saati (UTC)
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
        # Süresi dolmuş etkinlikleri sil
        utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
        events_collection.delete_many({"end_time": {"$lt": utc_now}})  # Bitiş zamanı geçmiş etkinlikleri sil

        events = events_collection.find({"group_id": group_id})

        event_list = []
        for event in events:
            start_time_local = None
            end_time_local = None

            # "start_time" ve "end_time" verilerini kontrol et
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

        # Grup bilgilerini al
        group = group_collection.find_one({'_id': ObjectId(group_id)})
        if not group:
            return JsonResponse({'error': 'Grup bulunamadı.'}, status=404)

        username = request.POST.get('username')
        current_user = request.session.get('username')

        # Kullanıcı kontrolü
        if group['owner'] != current_user:
            return JsonResponse({'error': 'Yalnızca grup sahibi üye çıkarabilir.'}, status=403)

        if username == group['owner']:
            return JsonResponse({'error': 'Grup sahibi gruptan çıkarılamaz.'}, status=400)

        # Üye grupta mı kontrol et
        if username in group['members']:
            group_collection.update_one(
                {'_id': ObjectId(group_id)},
                {'$pull': {'members': username}}  # Üyeyi gruptan çıkar
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
    user = request.session.get('username')  # Get the username from the session
    if user:
        try:
            # Correct query using count_documents() instead of count
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
    timeout_duration = 10  # Timeout duration of 10 seconds

    while True:
        messages = list(messages_collection.find(query).sort('timestamp', 1))  # MongoDB query

        if messages:
            formatted_messages = [
                {'sender': msg['sender'], 'text': msg['text'], 'timestamp': msg['timestamp']}
                for msg in messages
            ]
            return JsonResponse({'messages': formatted_messages})

        if time.time() - start_time > timeout_duration:
            return JsonResponse({'messages': []})  # Return empty if no new messages within the timeout

        time.sleep(1)
@csrf_exempt
def send_group_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        group_id = data.get('group_id')
        text = data.get('text')
        user = request.session.get('username')

        if user:
            # Save the message to MongoDB
            messages_collection.insert_one({
                'group_id': group_id,
                'sender': user,
                'text': text,
                'timestamp': datetime.now()
            })
            return JsonResponse({'status': 'success'})

        return JsonResponse({'status': 'error', 'message': 'User not authenticated.'}, status=401)