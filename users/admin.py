from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('email', 'avatar', 'bio')}),
        ('角色信息', {'fields': ('role', 'student_id', 'department', 'major', 'grade')}),
        ('权限信息', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # 创建新用户时
            if obj.role == 'teacher':
                obj.is_staff = True  # 教师自动设置为staff
            elif obj.role == 'admin':
                obj.is_staff = True  # 管理员自动设置为staff
                obj.is_superuser = True  # 管理员自动设置为superuser
            else:
                obj.is_staff = False  # 学生不是staff
        else:  # 编辑现有用户时
            if obj.role == 'admin':
                obj.is_staff = True
                obj.is_superuser = True
            elif obj.role == 'teacher':
                obj.is_staff = True
                obj.is_superuser = False
            else:
                obj.is_staff = False
                obj.is_superuser = False
        super().save_model(request, obj, form, change) 