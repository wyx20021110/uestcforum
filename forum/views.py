from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import Post, Comment, Category, Attachment
from .forms import PostForm, CommentForm
import logging
import json
import traceback

logger = logging.getLogger(__name__)

def post_list(request):
    """帖子列表视图"""
    search_query = request.GET.get('search', '')
    posts = Post.objects.all().order_by('-created_at')
    
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) | 
            Q(content__icontains=search_query) |
            Q(author__username__icontains=search_query)
        )
    
    # 分页
    paginator = Paginator(posts, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    context = {
        'posts': posts,
        'search_query': search_query
    }
    return render(request, 'forum/post_list.html', context)

def post_detail(request, pk):
    """帖子详情视图"""
    post = get_object_or_404(Post, pk=pk)
    context = {
        'post': post,
        'comment_form': CommentForm()
    }
    return render(request, 'forum/post_detail.html', context)

class PostCreateView(LoginRequiredMixin, CreateView):
    """创建帖子视图"""
    model = Post
    form_class = PostForm
    template_name = 'forum/post_form.html'
    success_url = reverse_lazy('forum:post_list')
    
    def form_valid(self, form):
        try:
            form.instance.author = self.request.user
            response = super().form_valid(form)
            
            # 处理附件上传
            attachments = self.request.FILES.getlist('attachments')
            for attachment in attachments:
                try:
                    Attachment.objects.create(
                        post=self.object,
                        file=attachment,
                        filename=attachment.name
                    )
                    logger.info(f"Successfully uploaded attachment: {attachment.name}")
                except Exception as e:
                    logger.error(f"Error uploading attachment {attachment.name}: {str(e)}")
                    messages.error(self.request, f'附件 {attachment.name} 上传失败')
            
            messages.success(self.request, '帖子发布成功！')
            return response
        except Exception as e:
            logger.error(f"Error creating post: {str(e)}")
            messages.error(self.request, '帖子发布失败，请重试')
            return self.form_invalid(form)

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """更新帖子视图"""
    model = Post
    form_class = PostForm
    template_name = 'forum/post_form.html'
    success_url = reverse_lazy('forum:post_list')
    
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_staff
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # 处理附件上传
        attachments = self.request.FILES.getlist('attachments')
        for attachment in attachments:
            Attachment.objects.create(
                post=self.object,
                file=attachment,
                filename=attachment.name
            )
        
        messages.success(self.request, '帖子更新成功！')
        return response

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """删除帖子视图"""
    model = Post
    success_url = reverse_lazy('forum:post_list')
    
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, '帖子删除成功！')
        return response

@login_required
def post_like(request, pk):
    # 记录请求信息，帮助调试
    logger.info(f"收到点赞请求 - 文章ID: {pk}, 用户: {request.user.username}, AJAX: {request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")
    logger.info(f"请求方法: {request.method}")
    logger.info(f"请求头: {dict(request.headers)}")
    
    # 记录请求体
    body_data = request.body.decode('utf-8') if request.body else 'Empty'
    logger.info(f"请求体: {body_data}")
    
    # 检查POST数据
    logger.info(f"POST数据: {dict(request.POST)}")
    logger.info(f"请求中的post_id: {request.POST.get('post_id')}")
    
    try:
        post = get_object_or_404(Post, pk=pk)
        
        # 记录找到的文章信息
        logger.info(f"找到文章: {post.id}, 标题: {post.title}, 作者: {post.author.username}")
        
        # 检查用户是否已经点赞
        like_exists = post.likes.filter(id=request.user.id).exists()
        logger.info(f"用户已点赞状态: {like_exists}")
        
        if like_exists:
            # 取消点赞
            post.likes.remove(request.user)
            logger.info(f"已取消点赞 - 文章ID: {pk}, 用户: {request.user.username}")
            is_liked = False
        else:
            # 添加点赞
            post.likes.add(request.user)
            logger.info(f"已添加点赞 - 文章ID: {pk}, 用户: {request.user.username}")
            is_liked = True
        
        # 获取最新点赞数
        likes_count = post.likes.count()
        logger.info(f"更新后点赞数: {likes_count}")
        
        # 返回JSON响应
        data = {
            'status': 'success',
            'likes_count': likes_count,
            'is_liked': is_liked
        }
        logger.info(f"返回成功响应: {data}")
        return JsonResponse(data)
        
    except Exception as e:
        # 记录详细错误信息
        error_msg = str(e)
        logger.error(f"点赞处理失败: {error_msg}")
        logger.error(traceback.format_exc())
        
        # 返回错误响应
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            data = {
                'status': 'error',
                'message': f'服务器错误: {error_msg}'
            }
            logger.info(f"返回错误响应: {data}")
            return JsonResponse(data, status=500)
        else:
            # 非AJAX请求返回普通错误页面
            messages.error(request, f'点赞失败: {error_msg}')
            return redirect('forum:post_detail', pk=pk)

@login_required
@require_POST
def comment_create(request, post_pk):
    """创建评论视图"""
    post = get_object_or_404(Post, pk=post_pk)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    logger.info(f"评论请求 - 帖子ID: {post_pk}, 用户: {request.user.username}, AJAX: {is_ajax}")
    
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        
        logger.info(f"评论发表成功 - ID: {comment.id}")
        
        if is_ajax:
            # 返回JSON响应
            data = {
                'status': 'success',
                'comment_id': comment.id,
                'content': comment.content,
                'author': comment.author.username,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
                'comment_count': post.comments.count()
            }
            return JsonResponse(data)
        else:
            messages.success(request, '评论发表成功！')
    else:
        error_msg = '\n'.join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()])
        logger.error(f"评论表单验证失败: {error_msg}")
        
        if is_ajax:
            # 返回错误JSON响应
            return JsonResponse({
                'status': 'error',
                'errors': form.errors
            }, status=400)
        else:
            messages.error(request, '评论内容不能为空！')
    
    # 非AJAX请求返回到用户来源页面
    if not is_ajax:
        next_url = request.META.get('HTTP_REFERER')
        if next_url:
            return redirect(next_url)
        return redirect('forum:post_detail', pk=post_pk)

class CommentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """更新评论视图"""
    model = Comment
    form_class = CommentForm
    template_name = 'forum/comment_form.html'
    
    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.author or self.request.user.is_staff
    
    def get_success_url(self):
        return reverse_lazy('forum:post_detail', kwargs={'pk': self.object.post.pk})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '评论更新成功！')
        return response

class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """删除评论视图"""
    model = Comment
    
    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.author or self.request.user.is_staff
    
    def get_success_url(self):
        return reverse_lazy('forum:post_detail', kwargs={'pk': self.object.post.pk})
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, '评论删除成功！')
        return response

@login_required
@require_POST
def attachment_delete(request, pk):
    """删除附件视图"""
    attachment = get_object_or_404(Attachment, pk=pk)
    post = attachment.post
    
    if request.user == post.author or request.user.is_staff:
        attachment.delete()
        messages.success(request, '附件删除成功！')
    else:
        messages.error(request, '您没有权限删除此附件！')
    
    return redirect('forum:post_edit', pk=post.pk) 