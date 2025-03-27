from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .models import User
from .forms import UserRegistrationForm, UserProfileForm
from django.core.paginator import Paginator

def login_view(request):
    """用户登录视图"""
    if request.user.is_authenticated:
        return redirect('forum:post_list')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, '登录成功！')
            return redirect('forum:post_list')
        else:
            messages.error(request, '用户名或密码错误！')
    return render(request, 'users/login.html')

def logout_view(request):
    """用户登出视图"""
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, '已成功退出登录！')
    return redirect('forum:post_list')

class RegisterView(CreateView):
    """用户注册视图"""
    model = User
    form_class = UserRegistrationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '注册成功！请登录。')
        return response

@login_required
def profile_view(request):
    """用户资料视图"""
    # 获取当前用户的帖子，按创建时间倒序排列
    user_posts_list = request.user.post_set.all().order_by('-created_at')
    
    # 分页处理，每页显示5篇帖子
    paginator = Paginator(user_posts_list, 5)
    page = request.GET.get('page')
    user_posts = paginator.get_page(page)
    
    context = {
        'user_posts': user_posts,
        'is_own_profile': True
    }
    return render(request, 'users/profile.html', context)

@login_required
def change_password_view(request):
    """修改密码视图"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(old_password):
            messages.error(request, '原密码错误！')
            return redirect('users:change_password')
        
        if new_password != confirm_password:
            messages.error(request, '两次输入的密码不一致！')
            return redirect('users:change_password')
        
        if len(new_password) < 8:
            messages.error(request, '新密码至少需要8个字符！')
            return redirect('users:change_password')
        
        request.user.set_password(new_password)
        request.user.save()
        messages.success(request, '密码修改成功！请重新登录。')
        return redirect('users:login')
    
    return render(request, 'users/change_password.html')

@login_required
def profile_edit_view(request):
    """编辑个人资料视图"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '个人资料更新成功！')
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'users/profile_edit.html', {'form': form})

def user_profile_view(request, user_id):
    """查看指定用户的资料"""
    profile_user = get_object_or_404(User, id=user_id)
    
    # 获取该用户的帖子，按创建时间倒序排列
    user_posts_list = profile_user.post_set.all().order_by('-created_at')
    
    # 分页处理，每页显示5篇帖子
    paginator = Paginator(user_posts_list, 5)
    page = request.GET.get('page')
    user_posts = paginator.get_page(page)
    
    context = {
        'user': profile_user,
        'user_posts': user_posts,
        'is_own_profile': request.user.id == profile_user.id if request.user.is_authenticated else False
    }
    return render(request, 'users/profile.html', context) 