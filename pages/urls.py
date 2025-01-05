from django.urls import path
from . import views
from djangoProject.consumers import ChatConsumer, GroupChatConsumer
from .views import logout, group_detail, request_membership, manage_requests, approve_request, reject_request, \
    get_membership_requests,send_friend_request, accept_friend_request, \
    reject_friend_request, search_friends, profile_view, fetch_group_messages, send_group_message, \
    leave_group, remove_member, create_event, get_events, post_view, delete_account
from .views import add_group
from django.conf import settings
from django.conf.urls.static import static
from .views import like_post
from .views import upload_profile_picture
urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),
    path('signup/', views.signup, name='signup'),
    path('register/', views.register, name='register'),
    path('home/', views.home, name='home'),
    path('topics/', views.topic, name='topics'),
    path('api/create_topic/', views.create_topic, name='create_topic'),
    path('api/get_topics/', views.get_topics, name='get_topics'),
    path('api/add_comment_topic/', views.add_comment_topic, name='add_comment_topic'),
    path('api/get_comments_for_topic/<str:topic_id>/', views.get_comments_for_topic, name='get_comments_for_topic'),
    path('api/like_topic/<str:topic_id>/', views.like_topic, name='like_topic'),
    path('api/dislike_topic/<str:topic_id>/', views.dislike_topic, name='dislike_topic'),
    path('topics/', views.list_topics, name='topics'),
    path('add_post/', views.add_post, name='add_post'),
    path('logout/', logout, name='logout'),
    path('post_view/', post_view, name='post_view'),
    path('post/<str:post_id>/', views.post_view, name='post_view'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<str:username>/', profile_view, name='profile_view'),
    path('add_group/', add_group, name='add_group'),
    path('group/<str:group_id>/', group_detail, name='group_detail'),
    path('group/<str:group_id>/request_membership/', request_membership, name='request_membership'),
    path('group/<str:group_id>/manage_requests/', manage_requests, name='manage_requests'),
    path('group/<str:group_id>/membership_requests/', get_membership_requests, name='get_membership_requests'),
    path('create_event/',   create_event, name='create_event'),
    path('get_events/', get_events, name='get_events'),
    path('request/<str:request_id>/approve/', approve_request, name='approve_request'),
    path('request/<str:request_id>/reject/', reject_request, name='reject_request'),
    path('send_friend_request/<str:username>/', send_friend_request, name='send_friend_request'),
    path('friend_request/<str:request_id>/accept/', accept_friend_request, name='accept_friend_request'),
    path('friend_request/<str:request_id>/reject/', reject_friend_request, name='reject_friend_request'),
    path('search_friends/', search_friends, name='search_friends'),
    path('send_friend_request/<str:username>/', send_friend_request, name='send_friend_request'),
    path('send_message/', views.send_message, name='send_message'),
    path('chat/fetch_messages/', views.fetch_messages, name='fetch_messages'),
    path('chat/send_message/', views.send_message, name='send_message'),
    path('send_message/', views.send_message, name='send_message'),
    path('fetch_messages/', views.fetch_messages, name='fetch_messages'),
    path('like_post/', like_post, name='like_post'),
    path('upload_profile_picture/', upload_profile_picture, name='upload_profile_picture'),
    path('check-new-messages/', views.check_new_messages, name='check_new_messages'),
    path('mark_messages_as_read/<str:sender>/<str:recipient>/', views.mark_messages_as_read_view,
         name='mark_messages_as_read'),
    path('add_comment/', views.add_comment, name='add_comment'),
    path('fetch-group-messages/', fetch_group_messages, name='fetch_group_messages'),
    path('send-group-message/', send_group_message, name='send_group_message'),
    path('leave_group/<str:group_id>/', leave_group, name='leave_group'),
    path('remove-member/<str:group_id>/', remove_member, name='remove_member'),
    path('remove_friend/', views.remove_friend, name='remove_friend'),
    path('delete_post/', views.delete_post, name='delete_post'),
    path('delete_account/', delete_account, name='delete_account'),
    path('get_membership_requests/<str:group_id>/', views.get_membership_requests, name='get_membership_requests')

]
websocket_urlpatterns = [
    path('ws/chat/<str:friend_username>/', ChatConsumer.as_asgi()),
    path('ws/group/<group_id>/', GroupChatConsumer.as_asgi()),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.PPS_URL, document_root=settings.PPS_ROOT)
