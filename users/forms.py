from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class UserRegistrationForm(UserCreationForm):
    """用户注册表单"""
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = 'student'  # 默认设置为学生角色
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    """用户资料表单"""
    class Meta:
        model = User
        fields = [
            'username', 
            'email', 
            'student_id', 
            'department', 
            'major', 
            'grade',
            'avatar', 
            'bio'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入学号/工号'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入所属院系'}),
            'major': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入专业'}),
            'grade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入年级，如2020级'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '简单介绍一下自己吧...'}),
        }
        labels = {
            'username': '用户名',
            'email': '电子邮箱',
            'student_id': '学号/工号',
            'department': '院系',
            'major': '专业',
            'grade': '年级',
            'avatar': '头像',
            'bio': '个人简介',
        }
        help_texts = {
            'username': '您的用户名将在平台中显示',
            'email': '用于接收通知和找回密码',
            'student_id': '您的学号或工号',
            'avatar': '推荐上传正方形图片',
            'bio': '最多500字',
        } 