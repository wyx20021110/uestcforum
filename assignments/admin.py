from django.contrib import admin
from .models import Assignment, Question, Choice, Submission, Answer

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'type', 'teacher', 'start_time', 'end_time', 'total_score', 'is_active']
    list_filter = ['type', 'teacher', 'start_time', 'end_time']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at']
    
    def is_active(self, obj):
        return obj.is_active
    is_active.boolean = True
    is_active.short_description = '是否进行中'

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'type', 'content', 'score', 'order']
    list_filter = ['type', 'assignment']
    search_fields = ['content']
    ordering = ['assignment', 'order']

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['question', 'content', 'is_correct', 'order']
    list_filter = ['is_correct', 'question']
    search_fields = ['content']
    ordering = ['question', 'order']

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'student', 'submitted_at', 'score', 'is_graded', 'is_late']
    list_filter = ['assignment', 'student', 'submitted_at', 'score']
    search_fields = ['student__username', 'feedback']
    readonly_fields = ['submitted_at']
    
    def is_graded(self, obj):
        return obj.score is not None
    is_graded.boolean = True
    is_graded.short_description = '是否已评分'
    
    def is_late(self, obj):
        return obj.submitted_at > obj.assignment.end_time
    is_late.boolean = True
    is_late.short_description = '是否迟交'

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['submission', 'question', 'score', 'is_correct']
    list_filter = ['question', 'score']
    search_fields = ['content']
    readonly_fields = ['submission', 'question']
    
    def is_correct(self, obj):
        if obj.question.type == 'choice':
            return obj.selected_choices.filter(is_correct=True).exists()
        return None
    is_correct.boolean = True
    is_correct.short_description = '是否正确' 