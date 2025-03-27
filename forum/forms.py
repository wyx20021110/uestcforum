from django import forms
from .models import Post, Comment

class PostForm(forms.ModelForm):
    """动态表单"""
    title = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '标题（可选）'
        }),
        label='标题'
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': '分享你的想法...'
        }),
        label='内容'
    )
    attachments = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control'
        }),
        label='上传图片/文件'
    )
    
    class Meta:
        model = Post
        fields = ['title', 'content']
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content) < 1:
            raise forms.ValidationError('内容不能为空')
        return content

class CommentForm(forms.ModelForm):
    """评论表单"""
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '写下你的评论...'
            }),
        }
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content) < 1:
            raise forms.ValidationError('评论内容不能为空')
        return content 