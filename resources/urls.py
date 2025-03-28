from django.urls import path
from . import views

app_name = 'resources'

urlpatterns = [
    # 资源相关
    path('', views.ResourceListView.as_view(), name='resource_list'),
    path('create/', views.ResourceCreateView.as_view(), name='resource_create'),
    path('<int:pk>/', views.ResourceDetailView.as_view(), name='resource_detail'),
    path('<int:pk>/edit/', views.ResourceUpdateView.as_view(), name='resource_edit'),
    path('<int:pk>/delete/', views.ResourceDeleteView.as_view(), name='resource_delete'),
    path('<int:pk>/download/', views.resource_download, name='resource_download'),
    path('<int:pk>/like/', views.resource_like, name='resource_like'),
    
    # 分类相关
    path('category/<slug:slug>/', views.ResourceListView.as_view(), name='resource_list_by_category'),
    path('uploader/<str:username>/', views.ResourceListView.as_view(), name='resource_list_by_uploader'),
    
    # 评论相关
    path('<int:pk>/comment/', views.comment_create, name='comment_create'),
    path('comments/<int:pk>/edit/', views.CommentUpdateView.as_view(), name='comment_edit'),
    path('comments/<int:pk>/delete/', views.CommentDeleteView.as_view(), name='comment_delete'),
] 