from django import forms
from django.forms import inlineformset_factory
from .models import Assignment, Question, Choice, Submission, Answer

class AssignmentForm(forms.ModelForm):
    """作业/考试表单"""
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'type', 'start_time', 'end_time', 'total_score']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError('结束时间必须晚于开始时间')
        
        return cleaned_data

class QuestionForm(forms.ModelForm):
    """题目表单"""
    class Meta:
        model = Question
        fields = ['content', 'type', 'score', 'order']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'score': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
            'order': forms.HiddenInput(),
        }

class ChoiceForm(forms.ModelForm):
    """选项表单"""
    class Meta:
        model = Choice
        fields = ['content', 'is_correct']
        widgets = {
            'content': forms.TextInput(attrs={'class': 'form-control'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class AnswerForm(forms.ModelForm):
    """答案表单"""
    class Meta:
        model = Answer
        fields = ['text_answer', 'selected_choices']
        widgets = {
            'text_answer': forms.Textarea(attrs={'rows': 3}),
            'selected_choices': forms.CheckboxSelectMultiple(),
        }

class GradeForm(forms.ModelForm):
    """评分表单"""
    class Meta:
        model = Answer
        fields = ['score', 'comment']
        widgets = {
            'score': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
    
    def clean_score(self):
        score = self.cleaned_data.get('score')
        question = self.instance.question
        
        if score is not None:
            if score < 0:
                raise forms.ValidationError('分数不能为负数')
            if score > question.score:
                raise forms.ValidationError(f'分数不能超过题目满分（{question.score}分）')
        
        return score

ChoiceFormSet = inlineformset_factory(
    Question,
    Choice,
    form=ChoiceForm,
    extra=4,
    can_delete=True,
    min_num=1,
    validate_min=True,
    fields=['content', 'is_correct'],
    exclude=None
) 