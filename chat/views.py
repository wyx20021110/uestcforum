from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.db.models import Q, Count, Max, F, Value, CharField
from django.db.models.functions import Concat
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import ChatRoom, Message
from django.views.decorators.http import require_POST
import json
from django.contrib import messages

User = get_user_model()

@login_required
def index(request):
    """聊天首页，显示用户的所有聊天室"""
    # 获取用户所有聊天室
    chat_rooms = ChatRoom.objects.filter(
        participants=request.user
    ).annotate(
        unread_count=Count(
            'messages',
            filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user)
        ),
        last_message_time=Max('messages__timestamp'),
        last_message=Max('messages__content')
    ).order_by('-last_message_time')
    
    # 遍历聊天室，为每个私聊添加其他参与者信息
    for room in chat_rooms:
        if room.is_private and room.participants.count() == 2:
            room.other_participant = room.participants.exclude(id=request.user.id).first()
    
    # 查找可以聊天的用户（比如同班同学、老师等，这里简化为所有用户）
    available_users = User.objects.exclude(id=request.user.id)
    
    # 获取所有用户的头像信息用于WebSocket通信
    user_avatars = {}
    all_users = User.objects.all()
    for user in all_users:
        if user.avatar:
            user_avatars[user.username] = user.avatar.url
    
    context = {
        'chat_rooms': chat_rooms,
        'available_users': available_users,
        'user_avatars': json.dumps(user_avatars)
    }
    
    return render(request, 'chat/index.html', context)

@login_required
def api_room_detail(request, room_id):
    """获取聊天室详细信息的API端点"""
    try:
        room = get_object_or_404(ChatRoom, id=room_id)
        
        # 检查用户是否有权限访问
        if request.user not in room.participants.all():
            return JsonResponse({
                'status': 'error', 
                'message': '无权访问此聊天室'
            }, status=403)
        
        # 获取聊天对象（在私聊情况下）
        chat_with = None
        if room.is_private and room.participants.count() == 2:
            chat_with = room.participants.exclude(id=request.user.id).first()
            
        # 构建响应数据
        response_data = {
            'status': 'success',
            'room': {
                'id': room.id,
                'name': room.name,
                'is_private': room.is_private,
                'participants_count': room.participants.count()
            }
        }
        
        if chat_with:
            response_data['chat_with'] = {
                'id': chat_with.id,
                'username': chat_with.username
            }
        
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
@require_POST
def create_private_chat(request):
    """创建私聊"""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        if not user_id:
            return JsonResponse({'status': 'error', 'message': '未提供用户ID'}, status=400)
        
        # 确保user_id是整数
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return JsonResponse({'status': 'error', 'message': '无效的用户ID'}, status=400)
        
        # 检查用户是否存在
        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '用户不存在'}, status=404)
        
        # 检查是否尝试与自己聊天
        if request.user.id == user_id:
            return JsonResponse({'status': 'error', 'message': '不能与自己创建私聊'}, status=400)
        
        # 检查是否已经存在私聊
        existing_room = ChatRoom.objects.filter(
            is_private=True,
            participants=request.user
        ).filter(
            participants=other_user
        ).first()
        
        if existing_room:
            return JsonResponse({
                'status': 'success', 
                'room_id': existing_room.id,
                'message': '聊天室已存在'
            })
        
        # 创建新的私聊
        room_name = f"{request.user.username} & {other_user.username}"
        room = ChatRoom.objects.create(
            name=room_name,
            is_private=True
        )
        room.participants.add(request.user, other_user)
        
        return JsonResponse({
            'status': 'success',
            'room_id': room.id,
            'message': '聊天室已创建'
        })
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': '无效的请求格式'}, status=400)
    except Exception as e:
        # 记录错误但不暴露详细信息给用户
        print(f"创建私聊错误: {str(e)}")
        return JsonResponse({'status': 'error', 'message': '服务器处理请求时出错'}, status=500)

@login_required
@require_POST
def create_group_chat(request):
    """创建群聊"""
    try:
        data = json.loads(request.body)
        name = data.get('name')
        description = data.get('description', '')
        participant_ids = data.get('participants', [])
        
        if not name:
            return JsonResponse({'status': 'error', 'message': '未提供群聊名称'}, status=400)
        
        if not name.strip():
            return JsonResponse({'status': 'error', 'message': '群聊名称不能为空'}, status=400)
        
        if len(name) > 100:
            return JsonResponse({'status': 'error', 'message': '群聊名称过长，最多100个字符'}, status=400)
        
        # 验证参与者ID列表
        valid_participant_ids = []
        for pid in participant_ids:
            try:
                user_id = int(pid)
                # 验证用户是否存在
                if User.objects.filter(id=user_id).exists():
                    valid_participant_ids.append(user_id)
            except (ValueError, TypeError):
                continue  # 忽略无效ID
        
        # 创建群聊
        room = ChatRoom.objects.create(
            name=name,
            description=description,
            is_private=False
        )
        
        # 添加创建者
        room.participants.add(request.user)
        
        # 添加其他参与者
        if valid_participant_ids:
            participants = User.objects.filter(id__in=valid_participant_ids)
            for participant in participants:
                if participant.id != request.user.id:  # 确保不重复添加创建者
                    room.participants.add(participant)
        
        return JsonResponse({
            'status': 'success',
            'room_id': room.id,
            'message': '群聊已创建'
        })
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': '无效的请求格式'}, status=400)
    except Exception as e:
        # 记录错误但不暴露详细信息给用户
        print(f"创建群聊错误: {str(e)}")
        return JsonResponse({'status': 'error', 'message': '服务器处理请求时出错'}, status=500)

@login_required
def get_unread_count(request):
    """获取未读消息数量"""
    unread_count = Message.objects.filter(
        room__participants=request.user,
        is_read=False
    ).exclude(sender=request.user).count()
    
    return JsonResponse({'unread_count': unread_count})

@login_required
def help_page(request):
    """聊天帮助页面"""
    return render(request, 'chat/help.html')

@login_required
@require_POST
def create_room(request):
    """创建新聊天室（表单提交）"""
    room_name = request.POST.get('room_name')
    description = request.POST.get('description', '')
    is_private = request.POST.get('is_private') == 'on'
    
    if not room_name or not room_name.strip():
        messages.error(request, '聊天室名称不能为空')
        return redirect('chat:index')
    
    if len(room_name) > 100:
        messages.error(request, '聊天室名称过长，最多100个字符')
        return redirect('chat:index')
    
    # 创建聊天室
    room = ChatRoom.objects.create(
        name=room_name,
        description=description,
        is_private=is_private
    )
    
    # 添加创建者为参与者
    room.participants.add(request.user)
    
    messages.success(request, f'聊天室 "{room_name}" 创建成功')
    return HttpResponseRedirect(reverse('chat:index') + f'?room={room.id}')

@login_required
@require_POST
def start_private_chat(request):
    """发起私聊（表单提交）"""
    username = request.POST.get('username')
    initial_message = request.POST.get('message', '')
    
    if not username:
        messages.error(request, '请选择要聊天的用户')
        return redirect('chat:index')
    
    # 查找用户
    try:
        other_user = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, f'用户 "{username}" 不存在')
        return redirect('chat:index')
    
    # 检查是否尝试与自己聊天
    if request.user.username == username:
        messages.error(request, '不能与自己创建私聊')
        return redirect('chat:index')
    
    # 检查是否已经存在私聊
    existing_room = ChatRoom.objects.filter(
        is_private=True,
        participants=request.user
    ).filter(
        participants=other_user
    ).first()
    
    # 如果存在私聊，直接使用它
    if existing_room:
        # 如果提供了初始消息，创建一条消息
        if initial_message and initial_message.strip():
            Message.objects.create(
                room=existing_room,
                sender=request.user,
                content=initial_message.strip()
            )
        return HttpResponseRedirect(reverse('chat:index') + f'?room={existing_room.id}')
    
    # 创建新的私聊
    room_name = f"{request.user.username} & {other_user.username}"
    room = ChatRoom.objects.create(
        name=room_name,
        is_private=True
    )
    room.participants.add(request.user, other_user)
    
    # 如果提供了初始消息，创建一条消息
    if initial_message and initial_message.strip():
        Message.objects.create(
            room=room,
            sender=request.user,
            content=initial_message.strip()
        )
    
    return HttpResponseRedirect(reverse('chat:index') + f'?room={room.id}')
