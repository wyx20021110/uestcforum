from django.contrib import admin
from .models import ResourceCategory, Resource, ResourceComment, ResourceRating

@admin.register(ResourceCategory)
class ResourceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name', 'description']

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'uploaded_by', 'download_count', 'like_count', 'created_at']
    list_filter = ['category', 'uploaded_by', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['download_count', 'like_count', 'created_at']
    
    def download_count(self, obj):
        return obj.download_count
    download_count.short_description = '下载次数'
    
    def like_count(self, obj):
        return obj.like_count
    like_count.short_description = '点赞数'

@admin.register(ResourceComment)
class ResourceCommentAdmin(admin.ModelAdmin):
    list_display = ['resource', 'user', 'content', 'created_at']
    list_filter = ['resource', 'user', 'created_at']
    search_fields = ['content']
    readonly_fields = ['created_at']

@admin.register(ResourceRating)
class ResourceRatingAdmin(admin.ModelAdmin):
    list_display = ('resource', 'user', 'rating', 'created_at')
    list_filter = ('resource', 'user', 'rating', 'created_at')
    search_fields = ('comment',)
    readonly_fields = ('created_at',)
    fieldsets = (
        ('评分信息', {
            'fields': ('rating', 'comment')
        }),
        ('关联信息', {
            'fields': ('resource', 'user')
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    ) 