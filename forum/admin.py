from django.contrib import admin
from .models import Category, Post, Comment, Attachment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'description')

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'views')
    list_filter = ('created_at',)
    search_fields = ('title', 'content')
    readonly_fields = ('views',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content', 'author__username')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author', 'post')

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'post', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('filename',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('post') 