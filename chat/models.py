from django.db import models
from django.conf import settings
from django.db.models.signals import post_migrate
from django.dispatch import receiver

class ChatRoom(models.Model):
    """聊天室模型，用于群组聊天"""
    name = models.CharField(max_length=100, verbose_name="聊天室名称")
    description = models.TextField(blank=True, null=True, verbose_name="聊天室描述")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='chat_rooms',
        verbose_name="参与者"
    )
    is_private = models.BooleanField(default=False, verbose_name="是否为私聊")
    
    class Meta:
        verbose_name = "聊天室"
        verbose_name_plural = "聊天室"
    
    def __str__(self):
        return self.name

class Message(models.Model):
    """聊天消息模型"""
    room = models.ForeignKey(
        ChatRoom, 
        on_delete=models.CASCADE, 
        related_name='messages',
        verbose_name="聊天室"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_messages',
        verbose_name="发送者"
    )
    content = models.TextField(verbose_name="消息内容")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="发送时间")
    is_read = models.BooleanField(default=False, verbose_name="是否已读")
    
    class Meta:
        verbose_name = "消息"
        verbose_name_plural = "消息"
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"

# 将信号接收器移到函数中避免循环导入
def register_signals():
    @receiver(post_migrate)
    def create_test_chat_room(sender, **kwargs):
        # 只有在chat应用迁移后执行
        if sender.name == 'chat':
            from django.apps import apps
            ChatRoom = apps.get_model('chat', 'ChatRoom')
            User = apps.get_model(settings.AUTH_USER_MODEL)
            
            # 检查是否已有测试聊天室
            if not ChatRoom.objects.filter(id=1).exists():
                # 创建测试聊天室
                room = ChatRoom.objects.create(
                    id=1,  # 确保ID为1
                    name="测试聊天室",
                    description="用于WebSocket连接测试的聊天室"
                )
                print(f"创建测试聊天室: {room.name} (ID: {room.id})")
                
                # 尝试添加系统用户或第一个用户作为参与者
                try:
                    # 获取管理员或第一个用户
                    user = User.objects.filter(is_superuser=True).first() or User.objects.first()
                    if user:
                        room.participants.add(user)
                        print(f"添加用户 {user.username} 到测试聊天室")
                except Exception as e:
                    print(f"无法添加用户到测试聊天室: {e}")
            else:
                print("测试聊天室已存在，跳过创建")

# 应用就绪后注册信号
from django.apps import AppConfig

class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'
    
    def ready(self):
        # 导入信号处理器
        register_signals()
