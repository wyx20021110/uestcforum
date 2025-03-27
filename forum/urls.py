from django.urls import path
from . import views

app_name = 'forum'

urlpatterns = [
    # 帖子相关
    path('', views.post_list, name='post_list'),
    path('posts/<int:pk>/', views.post_detail, name='post_detail'),
    path('posts/create/', views.PostCreateView.as_view(), name='post_create'),
    path('posts/<int:pk>/edit/', views.PostUpdateView.as_view(), name='post_edit'),
    path('posts/<int:pk>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    path('posts/<int:pk>/like/', views.post_like, name='post_like'),
    
    # 评论相关
    path('posts/<int:post_pk>/comments/create/', views.comment_create, name='comment_create'),
    path('comments/<int:pk>/edit/', views.CommentUpdateView.as_view(), name='comment_edit'),
    path('comments/<int:pk>/delete/', views.CommentDeleteView.as_view(), name='comment_delete'),
    
    # 附件相关
    path('attachments/<int:pk>/delete/', views.attachment_delete, name='attachment_delete'),
] 