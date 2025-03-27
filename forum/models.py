from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging
import os

User = get_user_model()

class Category(models.Model):
    """帖子分类"""
    name = models.CharField('分类名称', max_length=50)
    description = models.TextField('分类描述', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '分类'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

class Post(models.Model):
    """帖子"""
    title = models.CharField('标题', max_length=200)
    content = models.TextField('内容')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='作者')
    created_at = models.DateTimeField('发布时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True, verbose_name='点赞')
    views = models.PositiveIntegerField('浏览量', default=0)
    
    class Meta:
        verbose_name = '帖子'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def increment_views(self):
        """增加浏览量"""
        self.views += 1
        self.save()

class Comment(models.Model):
    """评论"""
    content = models.TextField('内容')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='作者')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='帖子')
    created_at = models.DateTimeField('发布时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '评论'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.author.username} 评论了 {self.post.title}'

class Attachment(models.Model):
    """附件"""
    file = models.FileField('文件', upload_to='forum/attachments/%Y/%m/%d/')
    filename = models.CharField('文件名', max_length=255)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='attachments', verbose_name='帖子')
    uploaded_at = models.DateTimeField('上传时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '附件'
        verbose_name_plural = verbose_name
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.filename
        
    def delete(self, *args, **kwargs):
        """重写删除方法，确保物理文件也被删除"""
        logger = logging.getLogger(__name__)
        
        # 记录删除信息
        logger.info(f"执行Attachment模型的自定义delete方法: file={self.file.name}")
        
        # 获取文件存储实例
        storage = self.file.storage
        
        # 保存文件名以便后续删除
        file_name = self.file.name
        
        # 先尝试关闭文件
        try:
            if hasattr(self.file, 'close'):
                self.file.close()
        except Exception as e:
            logger.error(f"关闭文件句柄失败: {str(e)}")
            
        # 执行标准删除操作，删除数据库记录
        super().delete(*args, **kwargs)
        
        # 删除物理文件
        try:
            # 方法1: 使用storage API
            if file_name and storage.exists(file_name):
                storage.delete(file_name)
                logger.info(f"使用storage API删除文件成功: {file_name}")
                
            # 方法2: 尝试使用os.remove作为备份
            if hasattr(self.file, 'path') and os.path.exists(self.file.path):
                os.remove(self.file.path)
                logger.info(f"使用os.remove删除文件成功: {self.file.path}")
                
        except Exception as e:
            logger.error(f"删除物理文件失败: {str(e)}")
            logger.exception("删除文件详细错误")

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('post', '帖子通知'),
        ('comment', '评论通知'),
        ('system', '系统通知'),
    )
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name='接收者')
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, verbose_name='通知类型')
    title = models.CharField(max_length=200, verbose_name='通知标题')
    content = models.TextField(verbose_name='通知内容')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    is_read = models.BooleanField(default=False, verbose_name='是否已读')
    
    class Meta:
        verbose_name = '通知'
        verbose_name_plural = '通知'
        ordering = ['-created_at']
        
    def __str__(self):
        return f'{self.recipient.username} - {self.title}' 