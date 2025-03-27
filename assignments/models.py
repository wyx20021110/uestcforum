from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import connection

class Assignment(models.Model):
    """作业/考试模型"""
    TYPE_CHOICES = (
        ('assignment', '作业'),
        ('exam', '考试'),
    )
    
    title = models.CharField('标题', max_length=200)
    description = models.TextField('描述', blank=True)
    type = models.CharField('类型', max_length=20, choices=TYPE_CHOICES, default='homework')
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assignments', verbose_name='教师')
    start_time = models.DateTimeField('开始时间')
    end_time = models.DateTimeField('结束时间')
    total_score = models.IntegerField('总分', default=100)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    last_modified = models.DateTimeField('最后题目修改时间', auto_now=True)
    
    class Meta:
        verbose_name = '作业'
        verbose_name_plural = '作业'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def is_active(self):
        """判断作业/考试是否在进行中"""
        now = timezone.now()
        return self.start_time <= now <= self.end_time
    
    @property
    def is_upcoming(self):
        return timezone.now() < self.start_time
    
    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError('结束时间必须晚于开始时间')
        
        # 只有在teacher字段被设置时才进行验证
        if hasattr(self, 'teacher') and self.teacher:
            if not self.teacher.is_teacher():
                raise ValidationError('只有教师可以创建作业')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class Question(models.Model):
    """题目模型"""
    TYPE_CHOICES = (
        ('single', '单选题'),
        ('multiple', '多选题'),
        ('text', '简答题'),
    )
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='questions')
    content = models.TextField(verbose_name='题目内容')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name='题目类型')
    score = models.IntegerField(verbose_name='分值')
    order = models.IntegerField(default=0, verbose_name='排序')
    
    class Meta:
        verbose_name = '题目'
        verbose_name_plural = verbose_name
        ordering = ['order']
    
    def __str__(self):
        return f'{self.assignment.title} - 第{self.order}题'
        
    def save(self, *args, **kwargs):
        # 如果是新创建的题目且order为0，设置为当前最大值+1
        if not self.pk and self.order == 0:
            last_question = Question.objects.filter(assignment=self.assignment).order_by('-order').first()
            self.order = (last_question.order + 1) if last_question else 1
        super().save(*args, **kwargs)

class Choice(models.Model):
    """选项模型"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    content = models.TextField(verbose_name='选项内容')
    is_correct = models.BooleanField(default=False, verbose_name='是否正确答案')
    order = models.IntegerField(default=0, verbose_name='排序')
    
    class Meta:
        verbose_name = '选项'
        verbose_name_plural = verbose_name
        ordering = ['order']
    
    def __str__(self):
        return f'{self.question.content[:50]} - {self.content[:50]}'

class Submission(models.Model):
    """提交记录模型"""
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    last_assignment_modified_at = models.DateTimeField('提交时作业版本', null=True, blank=True)
    
    class Meta:
        verbose_name = '提交记录'
        verbose_name_plural = '提交记录'
        ordering = ['-submitted_at']
        unique_together = ['assignment', 'student']
    
    def __str__(self):
        return f'{self.student.username} 提交了 {self.assignment.title}'
    
    @property
    def is_graded(self):
        """判断作业是否已评分"""
        return self.score is not None
    
    def clean(self):
        if not self.student.is_student():
            raise ValidationError('只有学生可以提交作业/考试')
        # 只在新创建记录时检查时间限制，而不是在更新记录（如评分）时
        if not self.pk and not self.assignment.is_active:
            raise ValidationError('作业/考试不在进行中')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class Answer(models.Model):
    """答案模型"""
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text_answer = models.TextField(blank=True, null=True, verbose_name='文本答案')
    selected_choices = models.ManyToManyField(Choice, blank=True, related_name='answers', verbose_name='选择的选项')
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='得分')
    comment = models.TextField(blank=True, null=True, verbose_name='评语')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '答案'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.submission.student.username} - {self.question.content[:50]}'

    def calculate_score(self):
        """计算得分（用于选择题的自动评分）"""
        print(f"计算答案{self.id}的得分，题目类型: {self.question.type}")
        
        if self.question.type == 'text':
            print("  跳过文本题自动评分")
            return None
        
        # 强制从数据库重新获取，确保数据最新
        self.refresh_from_db()
        
        with connection.cursor() as cursor:
            # 直接从数据库获取正确选项ID列表
            cursor.execute(
                "SELECT id FROM assignments_choice WHERE question_id = %s AND is_correct = %s",
                [self.question.id, True]
            )
            correct_choice_ids = {row[0] for row in cursor.fetchall()}
            
            # 直接从数据库获取已选择的选项ID列表
            cursor.execute(
                "SELECT choice_id FROM assignments_answer_selected_choices WHERE answer_id = %s",
                [self.id]
            )
            selected_choice_ids = {row[0] for row in cursor.fetchall()}
        
        print(f"  正确选项IDs: {correct_choice_ids}")
        print(f"  已选择选项IDs: {selected_choice_ids}")
        
        # 如果没有选择任何选项，得0分
        if not selected_choice_ids:
            print("  未选择任何选项，得分为0")
            return 0
            
        # 如果题目没有设置正确选项，返回None表示需要人工评分
        if not correct_choice_ids:
            print("  题目未设置正确选项，需要人工评分")
            return None
        
        if self.question.type == 'single':
            # 单选题：选择正确得满分，否则得0分
            is_correct = selected_choice_ids == correct_choice_ids
            score = self.question.score if is_correct else 0
            print(f"  单选题评分: 正确={is_correct}, 得分={score}")
            return score
        else:
            # 多选题：完全正确得满分，部分正确得部分分，有错误选项得0分
            total_correct = len(correct_choice_ids)
            correct_selected = len(selected_choice_ids & correct_choice_ids)
            incorrect_selected = len(selected_choice_ids - correct_choice_ids)
            
            print(f"  多选题评分: 总正确数={total_correct}, 正确选择数={correct_selected}, 错误选择数={incorrect_selected}")
            
            if incorrect_selected > 0:
                print("  选择了错误选项，得分为0")
                return 0
            
            # 避免除0错误
            if total_correct == 0:
                score = self.question.score if len(selected_choice_ids) == 0 else 0
                print(f"  题目无正确选项，得分={score}")
                return score
            
            # 计算部分得分
            score = float(self.question.score) * (correct_selected / total_correct)
            print(f"  部分得分: {score} = {self.question.score} * ({correct_selected}/{total_correct})")
            return score 