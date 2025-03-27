from django import forms
from .models import Resource, ResourceComment

class ResourceForm(forms.ModelForm):
    """资源表单"""
    class Meta:
        model = Resource
        fields = ['title', 'category', 'description', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入标题'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': '请输入资源描述'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 5:
            raise forms.ValidationError('标题至少需要5个字符')
        return title
    
    def clean_description(self):
        description = self.cleaned_data.get('description')
        if len(description) < 10:
            raise forms.ValidationError('描述至少需要10个字符')
        return description

class ResourceCommentForm(forms.ModelForm):
    """资源评论表单"""
    class Meta:
        model = ResourceComment
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
        if len(content) < 5:
            raise forms.ValidationError('评论内容至少需要5个字符')
        return content 