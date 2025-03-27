from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class ResourceCategory(models.Model):
    """资源分类"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = '资源分类'
        verbose_name_plural = '资源分类'
    
    def __str__(self):
        return self.name

class Resource(models.Model):
    """教学资源"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(ResourceCategory, on_delete=models.CASCADE, related_name='resources')
    file = models.FileField(upload_to='resources/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_resources', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    download_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_resources', blank=True)
    
    class Meta:
        verbose_name = '教学资源'
        verbose_name_plural = '教学资源'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def clean(self):
        if self.uploaded_by and not self.uploaded_by.is_teacher():
            raise ValidationError('只有教师可以上传教学资源')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class ResourceComment(models.Model):
    """资源评论"""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resource_comments', null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '资源评论'
        verbose_name_plural = '资源评论'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.user.username if self.user else "匿名用户"} 评论了 {self.resource.title}'

class ResourceRating(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='ratings', verbose_name='资源')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='评分用户')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name='评分')
    comment = models.TextField(blank=True, verbose_name='评价')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='评分时间')
    
    class Meta:
        verbose_name = '资源评分'
        verbose_name_plural = '资源评分'
        unique_together = ['resource', 'user']
        
    def __str__(self):
        return f'{self.user.username} 评分了 {self.resource.title}' 