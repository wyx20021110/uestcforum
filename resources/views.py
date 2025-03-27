from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import FileResponse, JsonResponse
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.decorators.http import require_POST
from .models import Resource, ResourceCategory, ResourceComment
from .forms import ResourceForm, ResourceCommentForm
import logging

logger = logging.getLogger(__name__)

def is_teacher(user):
    return user.is_authenticated and user.is_teacher()

class ResourceListView(ListView):
    model = Resource
    template_name = 'resources/resource_list.html'
    context_object_name = 'resources'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Resource.objects.all().order_by('-created_at')
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ResourceCategory.objects.all()
        return context

class ResourceDetailView(DetailView):
    model = Resource
    template_name = 'resources/resource_detail.html'
    context_object_name = 'resource'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = ResourceCommentForm()
        return context

class ResourceCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Resource
    form_class = ResourceForm
    template_name = 'resources/resource_form.html'
    success_url = reverse_lazy('resources:resource_list')
    
    def test_func(self):
        return is_teacher(self.request.user)
    
    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, '资源上传成功！')
        return super().form_valid(form)

class ResourceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Resource
    form_class = ResourceForm
    template_name = 'resources/resource_form.html'
    success_url = reverse_lazy('resources:resource_list')
    
    def test_func(self):
        return self.request.user == self.get_object().uploaded_by or self.request.user.is_admin()

class ResourceDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Resource
    success_url = reverse_lazy('resources:resource_list')
    
    def test_func(self):
        return self.request.user == self.get_object().uploaded_by or self.request.user.is_admin()

@login_required
def resource_download(request, pk):
    """下载资源视图"""
    resource = get_object_or_404(Resource, pk=pk)
    resource.download_count += 1
    resource.save()
    return FileResponse(resource.file, as_attachment=True)

@login_required
def resource_like(request, pk):
    """点赞资源视图"""
    try:
        resource = get_object_or_404(Resource, pk=pk)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # 记录请求信息到日志
        logger.info(f"点赞资源请求 - 资源ID: {pk}, 用户: {request.user.username}, AJAX: {is_ajax}")
        
        if request.user in resource.likes.all():
            resource.likes.remove(request.user)
            resource.like_count -= 1
            is_liked = False
            logger.info(f"用户 {request.user.username} 取消点赞资源 {pk}")
        else:
            resource.likes.add(request.user)
            resource.like_count += 1
            is_liked = True
            logger.info(f"用户 {request.user.username} 点赞资源 {pk}")
        resource.save()
        
        # 判断是否为AJAX请求
        if is_ajax:
            response_data = {
                'status': 'success',
                'is_liked': is_liked,
                'likes_count': resource.like_count
            }
            logger.info(f"返回AJAX响应: {response_data}")
            return JsonResponse(response_data)
        else:
            # 非AJAX请求的传统响应
            if is_liked:
                messages.success(request, '点赞成功')
            else:
                messages.success(request, '已取消点赞')
            return redirect('resources:resource_detail', pk=pk)
    except Exception as e:
        logger.error(f"资源点赞处理错误: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': '处理请求时出错'}, status=500)
        messages.error(request, '操作失败，请重试')
        return redirect('resources:resource_detail', pk=pk)

@login_required
def comment_create(request, pk):
    """创建评论视图"""
    resource = get_object_or_404(Resource, pk=pk)
    if request.method == 'POST':
        form = ResourceCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.resource = resource
            comment.user = request.user
            comment.save()
            messages.success(request, '评论发布成功！')
            return redirect('resources:resource_detail', pk=pk)
    else:
        form = ResourceCommentForm()
    return render(request, 'resources/resource_detail.html', {
        'resource': resource,
        'comment_form': form
    })

class CommentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ResourceComment
    form_class = ResourceCommentForm
    template_name = 'resources/comment_form.html'
    success_url = reverse_lazy('resources:resource_list')
    
    def test_func(self):
        return self.request.user == self.get_object().user or self.request.user.is_admin()

class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ResourceComment
    success_url = reverse_lazy('resources:resource_list')
    
    def test_func(self):
        return self.request.user == self.get_object().user or self.request.user.is_admin() 