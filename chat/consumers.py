import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message
from django.contrib.auth import get_user_model
import traceback
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.room_id = self.scope['url_route']['kwargs']['room_id']
            self.room_group_name = f'chat_{self.room_id}'
            
            # 检查用户是否有权限加入聊天室
            if not await self.has_permission():
                # 无权限情况下关闭连接
                await self.close(code=4003)
                return
            
            # 将用户加入聊天室群组
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            # 接受WebSocket连接
            await self.accept()
            
            # 发送聊天室历史消息
            history = await self.get_chat_history()
            await self.send(text_data=json.dumps({
                'type': 'chat_history',
                'messages': history
            }))
        except Exception as e:
            logger.error(f"WebSocket连接错误: {str(e)}")
            logger.error(traceback.format_exc())
            await self.close(code=4000)
    
    async def disconnect(self, close_code):
        try:
            # 断开连接时离开聊天室群组
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        except Exception as e:
            logger.error(f"WebSocket断开连接错误: {str(e)}")
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'chat_message')
            
            if message_type == 'chat_message':
                message = data.get('message', '').strip()
                
                # 忽略空消息
                if not message:
                    return
                
                # 保存消息到数据库
                await self.save_message(message)
                
                # 发送消息到群组
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'sender_id': self.scope['user'].id,
                        'sender_name': self.scope['user'].username,
                        'timestamp': await self.get_timestamp()
                    }
                )
            elif message_type == 'mark_read':
                # 标记消息为已读
                await self.mark_messages_read()
        except json.JSONDecodeError:
            # 忽略无效的JSON数据
            pass
        except Exception as e:
            logger.error(f"WebSocket接收消息错误: {str(e)}")
            logger.error(traceback.format_exc())
    
    async def chat_message(self, event):
        # 将消息发送到WebSocket
        try:
            await self.send(text_data=json.dumps({
                'type': 'chat_message',
                'message': event['message'],
                'sender_id': event['sender_id'],
                'sender_name': event['sender_name'],
                'timestamp': event['timestamp']
            }))
        except Exception as e:
            logger.error(f"WebSocket发送消息错误: {str(e)}")
    
    @database_sync_to_async
    def has_permission(self):
        try:
            user = self.scope['user']
            if not user.is_authenticated:
                return False
            
            room = ChatRoom.objects.get(id=self.room_id)
            return user in room.participants.all()
        except ChatRoom.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"检查权限错误: {str(e)}")
            return False
    
    @database_sync_to_async
    def save_message(self, content):
        try:
            user = self.scope['user']
            room = ChatRoom.objects.get(id=self.room_id)
            Message.objects.create(room=room, sender=user, content=content)
        except Exception as e:
            logger.error(f"保存消息错误: {str(e)}")
            raise
    
    @database_sync_to_async
    def get_chat_history(self):
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            messages = room.messages.select_related('sender').order_by('-timestamp')[:50]
            
            return [
                {
                    'message': msg.content,
                    'sender_id': msg.sender.id,
                    'sender_name': msg.sender.username,
                    'timestamp': msg.timestamp.isoformat(),
                    'is_read': msg.is_read
                }
                for msg in reversed(list(messages))
            ]
        except Exception as e:
            logger.error(f"获取聊天历史错误: {str(e)}")
            return []
    
    @database_sync_to_async
    def mark_messages_read(self):
        try:
            user = self.scope['user']
            room = ChatRoom.objects.get(id=self.room_id)
            
            # 将所有非当前用户发送的未读消息标记为已读
            Message.objects.filter(
                room=room,
                is_read=False
            ).exclude(sender=user).update(is_read=True)
        except Exception as e:
            logger.error(f"标记消息已读错误: {str(e)}")
    
    @database_sync_to_async
    def get_timestamp(self):
        try:
            from django.utils import timezone
            return timezone.now().isoformat()
        except Exception as e:
            logger.error(f"获取时间戳错误: {str(e)}")
            import datetime
            return datetime.datetime.now().isoformat() 