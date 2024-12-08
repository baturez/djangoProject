import base64
from datetime import datetime ,timedelta
from channels.db import database_sync_to_async
from django.http import JsonResponse, HttpResponseRedirect
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.shortcuts import render, redirect
from pymongo import MongoClient, DESCENDING
import bcrypt
from django.core.files.storage import FileSystemStorage
from .models import UserProfile
from django.utils.decorators import method_decorator
import pytz
from bson import ObjectId
from django.http import JsonResponse
from django.utils import timezone
from django.http import JsonResponse
import json
import asyncio
from djongo import models
from django import template
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from bson.objectid import ObjectId
from pymongo.errors import ConnectionFailure
from django.views.decorators.csrf import csrf_exempt
from .models import Message ,User
from . import save_post_to_mongo
import time
from bson.errors import InvalidId
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.contrib.sessions.models import Session
from django.contrib.auth import logout as auth_logout
from django.http import JsonResponse
from flask import Flask, request, jsonify, session

from django.db.models import Q
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
register = template.Library()
app = Flask(__name__)
app.secret_key = '856306'
MEMBERSHIP_REQUEST_COLLECTION = 'membership_requests'

@register.filter
@register.filter
def get_object_id(request):
    return str(request.get('_id')) if '_id' in request else None
def index(request):
    return render(request, "index.html")

def signup(request):
    return render(request, "sign_up.html")

def home(request):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    username = request.session.get('username')
    user_collection = db[USER_COLLECTION]
    user = user_collection.find_one({"username": username})

    current_user = user_collection.find_one({'username': username})
    friends = get_friends(current_user) if current_user else []

    post_collection = db[POST_COLLECTION]
    posts = post_collection.find().sort("created_at", -1)

    group_collection = db[GROUP_COLLECTION]
    groups = group_collection.find()

    return render(request, 'home_page.html', {
        'posts': posts,
        'groups': groups,
        'username': username,
        'current_user': current_user,
        'friends': friends
    })

def topic(request):
    username = request.session.get('username')
    user_collection = db[USER_COLLECTION]
    user = user_collection.find_one({"username": username})
    current_user = user_collection.find_one({'username': username})
    friends = get_friends(current_user) if current_user else []
    group_collection = db[GROUP_COLLECTION]
    groups = group_collection.find()
    return render(request, "topics.html" ,{
        'groups': groups,
        'username': username,
        'current_user': current_user,
        'friends': friends
    })





def get_topics(request):
    if request.method == 'GET':
        try:
            topics = list(db[TOPIC_COLLECTION].find())

            if not topics:
                return JsonResponse({'error': 'No topics found.'}, status=404)

            # Konuları düzenle
            for topic in topics:
                topic['_id'] = str(topic['_id'])
                topic['likes_count'] = len(topic.get('likes', []))
                topic['dislikes_count'] = len(topic.get('dislikes', []))

            return JsonResponse({'topics': topics}, safe=False)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)



def list_topics(request):
    topics = db[TOPIC_COLLECTION].find()
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
            likes = "0"
            dislikes = "0"

            new_topic = {
                'title': title,
                'description': description,
                'created_at': datetime.now(),
                'username': username,
                'comments': [],
                'comment_count': 0 ,
                'like': likes,
                'dislike': dislikes,
            }

            result = db[TOPIC_COLLECTION].insert_one(new_topic)
            topic_id = str(result.inserted_id)

            return JsonResponse({
                'success': True,
                'message': 'Topic created successfully!',
                'topic_id': topic_id,
                'likes': 0,
                'dislikes': 0
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

def get_comments(request, topic_id):
    try:
        comments = list(db[COMMENT_COLLECTION].find({'topic_id': ObjectId(topic_id)}))

        for comment in comments:
            comment['_id'] = str(comment['_id'])

        return JsonResponse({'comments': comments}, safe=False)
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

            likes = topic.get('likes', '0')
            likes_int = int(likes)
            likes_int += 1

            topic['dislikes'] = '0'

            updated_likes = str(likes_int)

            user_likes[username] = 'liked'

            db[TOPIC_COLLECTION].update_one(
                {'_id': ObjectId(topic_id)},
                {'$set': {'likes': updated_likes, 'user_likes': user_likes}}
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

            dislikes = topic.get('dislikes', '0')
            dislikes_int = int(dislikes)
            dislikes_int += 1

            topic['likes'] = '0'

            updated_dislikes = str(dislikes_int)

            user_likes[username] = 'disliked'

            db[TOPIC_COLLECTION].update_one(
                {'_id': ObjectId(topic_id)},
                {'$set': {'dislikes': updated_dislikes, 'user_likes': user_likes}}
            )

            return JsonResponse({'success': True, 'message': 'Topic disliked successfully!'}, status=200)

        except Exception as e:
            return JsonResponse({'success': False, 'error_message': str(e)}, status=400)



def register(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')

        if save_to_mongo(email, username, password):
            success_message = "Kayıt işlemi başarılı!"
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

        user_data = {
            "email": email,
            "username": username,
            "password": hashed_password,
            "friends": []
        }

        result = collection.insert_one(user_data)
        return result.acknowledged

    except ConnectionFailure as e:
        print(f"MongoDB bağlantı hatası: {e}")
        return False
    except Exception as e:
        print(f"Beklenmeyen bir hata oluştu: {e}")
        return False

@csrf_exempt
def upload_profile_picture(request):
    if request.method == 'POST' and request.FILES.get('profile_picture'):
        profile_picture = request.FILES['profile_picture']
        fs = FileSystemStorage(location=settings.PPS_ROOT)
        filename = fs.save(profile_picture.name, profile_picture)
        uploaded_file_url = fs.url(filename)

        username = request.session.get('username')
        UserProfile.objects.filter(username=username).update(profile_picture=uploaded_file_url)

        return HttpResponseRedirect('/profile/')

    return JsonResponse({'success': False, 'error_message': 'Geçersiz istek.'})
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
        user_collection = db[USER_COLLECTION]
        friend_request_collection = db[FRIEND_REQUEST_COLLECTION]
        group_collection = db['groups']
        groups = group_collection.find()
        user = user_collection.find_one({"username": username})

        # Arkadaşlık isteklerini al
        requests = list(friend_request_collection.find({'to_user': username, 'status': 'pending'}))

        # Arkadaşları al
        friends = get_friends(user)

        reqqq = friend_request_collection.find_one({}, {"_id": 1})

        if reqqq:
            reqqq = str(reqqq['_id'])

        if user:
            context = {
                'email': user['email'],
                'username': user['username'],
                'requests': requests,
                'reqqq': reqqq,
                'friends': friends,
                'groups' : groups
            }
            return render(request, 'profile.html', context)
        else:
            error_message = "Kullanıcı bulunamadı."
            return render(request, 'profile.html', {'error_message': error_message})
    else:
        return redirect('/login')
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

        current_user = request.session.get('username')

        pending_or_accepted_request = friend_request_collection.find_one({
            '$or': [
                {'from_user': current_user, 'to_user': username, 'status': {'$in': ['pending', 'accepted']}},
                {'from_user': username, 'to_user': current_user, 'status': {'$in': ['pending', 'accepted']}}
            ]
        })

        if pending_or_accepted_request:
            return JsonResponse({'success': False, 'error': 'Zaten arkadaşsınız ya da bir istek mevcut.'})
        else:
            friend_request = {
            'from_user': current_user,
            'to_user': username,
            'status': 'pending'
             }
            friend_request_collection.insert_one(friend_request)

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Geçersiz istek.'})





def view_friend_requests(request):
    username = request.session.get('username')
    if username:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        collection = db[FRIEND_REQUEST_COLLECTION]

        requests = list(collection.find({'to_user': username, 'status': 'pending'}))
        for req in requests:
            req['request_id'] = str(req['_id'])

        return render(request, 'friend_requests.html', {'requests': requests})

    return redirect('/login')

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
        user = user_collection.find_one({"username": usernamea})
        reqqq = friend_request_collection.find_one({}, {"status":1},sort=[("_id", DESCENDING)])
        friens = [friend['username'] for friend in get_friends(user)]
        friends = get_friends(user)
        results = list(collection.find({"username": {"$regex": search_query, "$options": "i"}}))

        return render(request, 'profile.html', {
            'search_results': results,
            'search_query': search_query,
            'username': usernamea,
            'friens': friens,
            'friends': friends,
            'user': user,
            'groups': groups,
            'reqq': reqqq
        })

    return redirect('profile')


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

def view_friends(request):
        username = request.session.get('username')
        if username:
            client = MongoClient(MONGO_URI)
            db = client[DATABASE_NAME]
            collection = db[FRIEND_REQUEST_COLLECTION]

            friends = list(collection.find({'$or': [{'from_user': username, 'status': 'accepted'},
                                                    {'to_user': username, 'status': 'accepted'}]}))
            return render(request, 'friends.html', {'friends': friends})

        return redirect('/login')

def groups(request):
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        group_collection = db['groups']
        groups = group_collection.find()

        return render(request, 'groups.html', {'groups': groups})




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

    return render(request, 'add_group.html', {'groups': group_list})



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

    return render(request, 'group_detail.html', {
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



@app.route('/check_request_status', methods=['GET'])
def check_request_status():
    group_id = request.args.get('group_id')
    user_username = request.args.get('user_username')

    # Check if a membership request exists for the given group and user
    existing_request = JOIN_REQUEST_COLLECTION.find_one({
        'group_id': group_id,
        'user_username': user_username
    })

    if existing_request:
        # Return the status of the existing request (e.g., 'pending', 'approved', 'rejected')
        return jsonify({'status': existing_request['status']})
    else:
        # No request found, return 'none'
        return jsonify({'status': 'none'})
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


@csrf_exempt
def send_message(request):
    if request.method == 'POST':
        try:
            message_data = json.loads(request.POST.get('message_data', '{}'))
            message_content = message_data.get('message')
            recipient = message_data.get('recipient')
            sender = message_data.get('sender')

            # Dosya işlemleri
            file = request.FILES.get('file')
            file_name = file.name if file else None
            file_size = file.size if file else None
            file_data = file.read() if file else None

            if not recipient or not sender or (not message_content and not file):
                return JsonResponse({'success': False, 'error': 'Eksik veri'}, status=400)

            # Mesajı MongoDB'ye kaydet
            message = {
                'sender': sender,
                'recipient': recipient,
                'text': message_content,
                'file_name': file_name,
                'file_size': file_size,
                'file_data': file_data,
                'timestamp': timezone.now()
            }
            messages_collection.insert_one(message)

            # WebSocket üzerinden mesajı gönder
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
                    'file_data': base64.b64encode(file_data).decode('utf-8') if file_data else None
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

        # Fetch messages from MongoDB
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
                'timestamp': msg['timestamp'].isoformat()
            }

            # Check if file data exists and encode to base64 if it's in bytes
            file_data = msg.get('file_data')
            if file_data:
                if isinstance(file_data, bytes):  # Ensure the file data is in bytes
                    formatted_message['file_data'] = base64.b64encode(file_data).decode('utf-8')
                else:
                    formatted_message['file_data'] = file_data  # Assume it's already a string (base64 encoded)

            formatted_messages.append(formatted_message)

        return JsonResponse({'messages': formatted_messages})

    except Exception as e:
        print(f"Error (fetch_messages): {e}")
        return JsonResponse({'success': False, 'error': 'Sunucu hatası'}, status=500)

@database_sync_to_async
def save_message(sender, recipient, message, file_name=None, file_size=None, file_data=None):
    message_data = {
        'sender': sender,
        'recipient': recipient,
        'text': message,
        'file_name': file_name,
        'file_size': file_size,
        'file_data': file_data,
        'timestamp': timezone.now()
    }
    messages_collection.insert_one(message_data)


@database_sync_to_async
def save_message(sender, recipient, message, file_name=None, file_size=None, file_data=None):
    # Eğer dosya verisi varsa, base64'ten byte dizisine dönüştür
    if file_data:
        try:
            file_data = base64.b64decode(file_data)  # Base64'ü tekrar byte dizisine çevir
            print("Decoded File Data Length:", len(file_data))  # Dosya uzunluğunu yazdır
        except Exception as e:
            print("Error decoding file data:", e)
            file_data = None  # Eğer bir hata varsa, dosya verisini None yap

    message_data = {
        'sender': sender,
        'recipient': recipient,
        'text': message,
        'file_name': file_name,
        'file_size': file_size,
        'file_data': file_data,
        'timestamp': timezone.now()
    }

    # MongoDB'ye veri kaydetme işlemi
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

# Send group message
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
