from django.contrib import admin
from .models import ChatRoom, Message

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'is_private')
    list_filter = ('is_private', 'created_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('participants',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'room', 'short_content', 'timestamp', 'is_read')
    list_filter = ('is_read', 'timestamp', 'room')
    search_fields = ('content', 'sender__username')
    
    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    
    short_content.short_description = '消息内容'
