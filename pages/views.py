from datetime import datetime
from django.http import JsonResponse, HttpResponseRedirect
from django.conf import settings

from django.shortcuts import render, redirect
from pymongo import MongoClient
import bcrypt
from django.core.files.storage import FileSystemStorage
from .models import UserProfile

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
from .models import ChatMessage
from django.db.models import Q
MONGO_URI = 'mongodb+srv://batuhanfahri06:PezQB4OKaTHSEjFm@bartini.qyrro.mongodb.net/?retryWrites=true&w=majority&appName=bartini'
DATABASE_NAME = 'my_database'
USER_COLLECTION = 'users'
POST_COLLECTION = 'posts'
GROUP_COLLECTION = 'groups'
TOPIC_COLLECTION = 'topics'
JOIN_REQUEST_COLLECTION = 'join_request'
FRIEND_REQUEST_COLLECTION = 'friend_requests'
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
messages_collection = db['messages']
register = template.Library()
@register.filter
@register.filter
def get_object_id(request):
    return str(request.get('_id')) if '_id' in request else None
def index(request):
    return render(request, "index.html")

def signup(request):
    return render(request, "sign_up.html")

def home(request):
    return render(request, "home_page.html")

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


def home(request):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    username = request.session.get('username')
    user_collection = db[USER_COLLECTION]
    user = user_collection.find_one({"username": username})

    current_user = user_collection.find_one({'username': username})
    friends = get_friends(current_user) if current_user else []

    # Postları çek
    post_collection = db[POST_COLLECTION]
    posts = post_collection.find().sort("created_at", -1)

    # Grupları çek
    group_collection = db[GROUP_COLLECTION]
    groups = group_collection.find()

    return render(request, 'home_page.html', {
        'posts': posts,
        'groups': groups,
        'username': username,
        'current_user': current_user,
        'friends': friends
    })

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

        groups = list(group_collection.find())
        usernamea = request.session.get('username')
        user = user_collection.find_one({"username": usernamea})

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
            'groups': groups
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
    membership_requests_collection = db['membership_requests']

    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        username = request.session.get('username')
        members = request.POST.getlist('members')

        if group_name and username:
            new_group = {
                'name': group_name,
                'owner': username,
                'members': members
            }
            group_collection.insert_one(new_group)
            return redirect('add_group')
        else:
            return render(request, 'add_group.html', {'error_message': 'Grup adı veya kullanıcı bilgisi eksik.'})

    groups = group_collection.find()

    group_list = [{'id': str(group['_id']), 'name': group['name']} for group in groups]

    return render(request, 'add_group.html', {'groups': group_list})


def group_detail(request, group_id):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    group_collection = db[GROUP_COLLECTION]
    group = group_collection.find_one({'_id': ObjectId(group_id)})

    group_id_str = str(group['_id'])

    username = request.session.get('username')

    user_username = username if username else 'Guest'

    return render(request, 'group_detail.html', {
        'group': group,
        'group_id_str': group_id_str,
        'user_username': user_username
    })
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
            data = json.loads(request.body)
            message_content = data.get('message')
            recipient = data.get('recipient')

            sender = request.session.get('username')

            if not message_content or not recipient or not sender:
                return JsonResponse({'success': False, 'error': 'Invalid input data'}, status=400)

            message = {
                'sender': sender,
                'recipient': recipient,
                'text': message_content,
                'timestamp': timezone.now()
            }
            messages_collection.insert_one(message)
            return JsonResponse({'success': True})

        except Exception as e:
            print(f"Error in send_message: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False}, status=400)


@csrf_exempt
def fetch_messages(request):
    friend = request.GET.get('friend')
    last_timestamp = request.GET.get('last_timestamp')

    user = request.session.get('username')

    query = {
        '$or': [
            {'sender': user, 'recipient': friend},
            {'sender': friend, 'recipient': user}
        ]
    }

    if last_timestamp:
        query['timestamp'] = {'$gt': last_timestamp}

    while True:
        messages = list(messages_collection.find(query).sort('timestamp', 1))

        if messages:
            formatted_messages = [
                {'sender': msg['sender'], 'text': msg['text'], 'timestamp': msg['timestamp']}
                for msg in messages
            ]
            return JsonResponse({'messages': formatted_messages})

        time.sleep(1)
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
