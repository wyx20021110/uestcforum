from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.index, name='index'),
    path('room/<int:room_id>/', views.room, name='room'),
    path('create-private-chat/', views.create_private_chat, name='create_private_chat'),
    path('create-group-chat/', views.create_group_chat, name='create_group_chat'),
    path('get-unread-count/', views.get_unread_count, name='get_unread_count'),
    path('help/', views.help_page, name='help'),
    path('api/room/<int:room_id>/', views.api_room_detail, name='api_room_detail'),
    path('create-room/', views.create_room, name='create_room'),
    path('start-private-chat/', views.start_private_chat, name='start_private_chat'),
] 