from django.core.management.base import BaseCommand
from assignments.models import Assignment, Question

class Command(BaseCommand):
    help = '修复所有题目的顺序问题，按照每个作业/考试重新设置题目序号'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('开始修复题目顺序...'))
        
        # 获取所有作业/考试
        assignments = Assignment.objects.all()
        self.stdout.write(f'找到 {assignments.count()} 个作业/考试')
        
        # 修复每个作业/考试的题目顺序
        for assignment in assignments:
            self.stdout.write(f'处理作业: {assignment.title}')
            
            # 按照当前的顺序获取题目
            questions = assignment.questions.all().order_by('order')
            
            # 重新设置顺序
            for index, question in enumerate(questions, 1):
                old_order = question.order
                question.order = index
                question.save(update_fields=['order'])
                self.stdout.write(f'  题目 ID:{question.id} 顺序从 {old_order} 修改为 {index}')
        
        self.stdout.write(self.style.SUCCESS('题目顺序修复完成！')) 