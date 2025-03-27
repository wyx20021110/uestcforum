from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.generic import UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from .models import Assignment, Submission, Question, Choice, Answer
from .forms import AssignmentForm, QuestionForm, ChoiceForm, ChoiceFormSet, AnswerForm, GradeForm
from django.db import transaction
from django.http import HttpResponseForbidden
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth import get_user_model

def is_teacher(user):
    return user.is_authenticated and user.is_teacher()

def is_student(user):
    return user.is_authenticated and user.is_student()

def assignment_list(request):
    """作业列表视图"""
    assignments = Assignment.objects.all().order_by('-created_at')
    context = {
        'assignments': assignments
    }
    return render(request, 'assignments/assignment_list.html', context)

@login_required
def assignment_create(request):
    """创建作业视图"""
    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.teacher = request.user
            assignment.save()
            messages.success(request, '作业创建成功！')
            return redirect('assignments:assignment_list')
    else:
        form = AssignmentForm()
    return render(request, 'assignments/assignment_form.html', {'form': form})

def _ensure_answers_for_submission(submission):
    """确保提交记录包含作业中所有题目的答案记录"""
    questions = submission.assignment.questions.all()
    created_answers = []
    
    print(f"检查提交{submission.id}的答案记录, 题目总数: {questions.count()}")
    
    for question in questions:
        answer, created = Answer.objects.get_or_create(
            submission=submission,
            question=question
        )
        if created:
            print(f"创建了新答案: 提交ID={submission.id}, 题目ID={question.id}, 答案ID={answer.id}")
            created_answers.append(answer)
    
    return created_answers

@login_required
def assignment_detail(request, pk):
    """作业详情视图"""
    assignment = get_object_or_404(Assignment, pk=pk)
    context = {'assignment': assignment}
    
    # 教师视图: 显示所有学生提交的内容和评分
    if request.user.is_teacher() or request.user.is_superuser:
        print(f"教师视图: 用户ID {request.user.id}, 作业ID {assignment.pk}")
        
        # 获取所有提交
        submissions = Submission.objects.filter(assignment=assignment)
        print(f"总提交数: {submissions.count()}")
        
        # 确保所有提交有完整的答案记录
        for submission in submissions:
            _ensure_answers_for_submission(submission)
        
        # 初始化统计数据
        graded_submissions = []
        ungraded_submissions = []
        
        # 分析每个提交的评分状态
        for submission in submissions:
            print(f"\n检查提交 ID: {submission.pk}, 学生: {submission.student.username}")
            print(f"  答案数量: {submission.answers.count()}")
            
            # 简化检测: 只要有一个未评分的答案或总分未设置，就认为是未评分提交
            has_unscored_answers = submission.answers.filter(score__isnull=True).exists()
            
            if has_unscored_answers or submission.score is None:
                print(f"  未评分: 有未评分答案={has_unscored_answers}, 总分未设置={submission.score is None}")
                ungraded_submissions.append(submission)
            else:
                print(f"  已评分: 总分={submission.score}")
                graded_submissions.append(submission)
            
            # 详细打印每个答案的状态，用于调试
            for answer in submission.answers.all():
                print(f"    答案ID: {answer.id}, 题目ID: {answer.question.id}, 类型: {answer.question.type}, 分数: {answer.score}")
                if answer.question.type in ['single', 'multiple']:
                    choices = [c.id for c in answer.selected_choices.all()]
                    print(f"      选择题选项: {choices}")
                elif answer.question.type == 'text':
                    print(f"      简答题内容: {answer.text_answer[:20] if answer.text_answer else '无'}")
        
        context.update({
            'submissions': submissions,
            'graded_submissions': graded_submissions,
            'ungraded_submissions': ungraded_submissions,
        })
        
        print(f"统计结果: 总提交数={submissions.count()}, 已评分={len(graded_submissions)}, 未评分={len(ungraded_submissions)}")
    
    # 学生视图: 显示个人提交的内容和评分
    else:
        print(f"学生视图: 用户ID {request.user.id}, 作业ID {assignment.pk}")
        submission = Submission.objects.filter(assignment=assignment, student=request.user).first()
        
        if submission:
            print(f"学生已提交: 提交ID={submission.id}, 评分状态={'已评分' if submission.score is not None else '未评分'}")
            # 确保所有题目都有答案记录
            _ensure_answers_for_submission(submission)
            
            # 为模板准备答案数据
            answers = {}
            for answer in submission.answers.all():
                answers[answer.question.id] = answer
                print(f"  答案: 题目ID={answer.question.id}, 类型={answer.question.type}, 得分={answer.score}")
            
            context.update({
                'submission': submission,
                'answers': answers,
            })
        else:
            print(f"学生尚未提交")
    
    print(f"渲染作业详情页面")
    return render(request, 'assignments/assignment_detail.html', context)

class AssignmentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """更新作业/考试视图"""
    model = Assignment
    form_class = AssignmentForm
    template_name = 'assignments/assignment_form.html'
    
    def get_success_url(self):
        return reverse_lazy('assignments:assignment_detail', kwargs={'pk': self.object.pk})
    
    def test_func(self):
        assignment = self.get_object()
        return self.request.user == assignment.teacher or self.request.user.is_admin()
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '作业/考试更新成功！')
        return response

class AssignmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """删除作业视图"""
    model = Assignment
    success_url = reverse_lazy('assignments:assignment_list')
    
    def test_func(self):
        assignment = self.get_object()
        return self.request.user == assignment.teacher or self.request.user.is_admin()
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, '作业删除成功！')
        return response

@login_required
def submit_assignment(request, pk):
    """提交作业视图"""
    assignment = get_object_or_404(Assignment, pk=pk)
    print(f"\n学生提交作业: 用户ID={request.user.id}, 用户名={request.user.username}, 作业ID={assignment.pk}")
    
    # 检查作业是否包含题目
    if not assignment.questions.exists():
        messages.error(request, "该作业没有包含任何题目，无法提交！")
        print(f"  错误: 作业没有题目")
        return redirect('assignments:assignment_detail', pk=pk)
    
    if not request.user.is_student():
        messages.error(request, '只有学生可以提交作业！')
        print(f"  错误: 用户不是学生角色，role={request.user.role}")
        return redirect('assignments:assignment_detail', pk=pk)
    
    # 检查作业是否在有效期内
    if not assignment.is_active:
        messages.error(request, '作业已截止或尚未开始，无法提交！')
        print(f"  错误: 作业不在有效提交期内，当前状态={'已截止' if timezone.now() > assignment.end_time else '未开始'}")
        return redirect('assignments:assignment_detail', pk=pk)
    
    # 获取所有作业的题目列表
    questions = assignment.questions.all().prefetch_related('choices')
    
    if request.method == 'POST':
        print(f"  处理POST提交请求")
        # 打印所有表单数据用于调试
        print(f"  表单数据: {request.POST}")

        # 验证表单数据
        form_is_valid = True
        
        # 检查每个题目是否有对应的表单项，并验证选项有效性
        for question in questions:
            field_name = f'answer_{question.id}'
            
            if question.type == 'text':
                answer_text = request.POST.get(field_name, '').strip()
                if not answer_text:
                    form_is_valid = False
                    print(f"  验证失败: 文本题 {question.id} 没有填写答案")
            elif question.type in ['single', 'multiple']:
                selected_choices = request.POST.getlist(field_name, [])
                
                # 验证是否选择了答案
                if not selected_choices:
                    form_is_valid = False
                    print(f"  验证失败: 选择题 {question.id} 没有选择任何答案")
                    continue
                    
                # 验证选项ID是否有效
                valid_choice_ids = set(str(choice.id) for choice in question.choices.all())
                for choice_id in selected_choices:
                    if choice_id not in valid_choice_ids:
                        form_is_valid = False
                        print(f"  验证失败: 选择题 {question.id} 提交了无效的选项ID: {choice_id}")
                        break
        
        if not form_is_valid:
            messages.error(request, '提交失败，请确保填写了所有题目并选择了有效的选项。')
            print("  表单验证失败，重新渲染提交页面")
            return render(request, 'assignments/submit_assignment.html', {
                'assignment': assignment,
                'forms': [(q, None) for q in questions]
            })
            
        try:
            with transaction.atomic():
                # 创建提交记录
                submission, created = Submission.objects.get_or_create(
                    assignment=assignment,
                    student=request.user,
                    defaults={
                        'score': None,
                        'last_assignment_modified_at': assignment.last_modified
                    }
                )
                
                print(f"  提交记录: ID={submission.id}, 新创建={created}, 作业ID={assignment.id}, 学生ID={submission.student.id}")
                
                # 如果不是新创建的提交，先清除旧的答案
                if not created:
                    old_answers_count = submission.answers.count()
                    submission.answers.all().delete()
                    # 更新最后修改时间
                    submission.last_assignment_modified_at = assignment.last_modified
                    print(f"  清除旧答案: {old_answers_count}个")
                
                total_score = 0
                has_text_questions = False
                all_questions_answered = True
                
                print(f"  开始处理每个题目的答案:")
                # 为所有题目创建答案记录
                for question in questions:
                    print(f"    处理题目: ID={question.id}, 类型={question.type}")
                    
                    answer = Answer.objects.create(
                        submission=submission,
                        question=question
                    )
                    print(f"    创建答案记录: ID={answer.id}")
                    
                    # 处理学生提交的答案
                    if question.type == 'text':
                        has_text_questions = True
                        answer_text = request.POST.get(f'answer_{question.id}')
                        print(f"    文本答案: {'已填写' if answer_text else '未填写'}, 值={answer_text}")
                        
                        if answer_text:
                            answer.text_answer = answer_text
                            answer.save()
                            print(f"    保存文本答案: 长度={len(answer_text)}")
                        else:
                            all_questions_answered = False
                            print(f"    警告: 文本题未作答")
                    elif question.type in ['single', 'multiple']:
                        selected_choices = request.POST.getlist(f'answer_{question.id}')
                        print(f"    选择题答案: 选择了{len(selected_choices)}个选项, 值={selected_choices}")
                        
                        if selected_choices:
                            # 确保选择的ID是整数
                            try:
                                choice_ids = []
                                valid_choice_ids = set(choice.id for choice in question.choices.all())
                                
                                for choice_id in selected_choices:
                                    if not choice_id.isdigit():
                                        print(f"    警告: 忽略非数字选项ID: {choice_id}")
                                        continue
                                        
                                    choice_id_int = int(choice_id)
                                    if choice_id_int in valid_choice_ids:
                                        choice_ids.append(choice_id_int)
                                    else:
                                        print(f"    警告: 忽略无效的选项ID: {choice_id_int}")
                                
                                print(f"    选择的有效选项IDs: {choice_ids}")
                                
                                if choice_ids:  # 只有当有有效选项时才设置
                                    answer.selected_choices.set(choice_ids)
                                    # 自动评分
                                    score = answer.calculate_score()
                                    if score is not None:
                                        answer.score = score
                                        answer.save()  # 确保保存评分
                                        print(f"    自动评分: 题目{question.id}, 得分{score}, 答案ID{answer.id}")
                                        total_score += float(score)
                                    else:
                                        print(f"    警告: 选择题未能自动评分")
                                else:
                                    all_questions_answered = False
                                    print(f"    警告: 没有有效的选择")
                            except Exception as choice_error:
                                print(f"    处理选择题选项时出错: {choice_error}")
                                all_questions_answered = False
                        else:
                            all_questions_answered = False
                            print(f"    警告: 选择题未选择答案")
                
                # 如果所有题目都是选择题并且都已回答，更新总分
                if not has_text_questions and all_questions_answered:
                    submission.score = total_score
                    submission.save()
                    print(f"  设置总分: {total_score}分")
                else:
                    print(f"  不设置总分: 有文本题={has_text_questions}, 所有题目已回答={all_questions_answered}")
                    # 确保即使没有设置总分也保存submission
                    submission.save()
                    
                messages.success(request, '作业提交成功！')
                if has_text_questions:
                    messages.info(request, '作业包含简答题，需要教师评分后才能查看总分。')
                
                print(f"  提交成功: 总分={total_score if not has_text_questions and all_questions_answered else '未设置'}")
                return redirect('assignments:assignment_detail', pk=pk)
        except Exception as e:
            import traceback
            print(f"  提交异常: {str(e)}")
            print(f"  异常详情: {traceback.format_exc()}")
            messages.error(request, f'提交作业失败：{str(e)}')
            return render(request, 'assignments/submit_assignment.html', {
                'assignment': assignment,
                'forms': [(q, None) for q in questions]
            })
    else:
        # GET请求，显示作业提交表单
        # 检查是否已有提交记录
        existing_submission = Submission.objects.filter(
            assignment=assignment,
            student=request.user
        ).first()
        
        print(f"GET请求: 已有提交={bool(existing_submission)}")
        
        if existing_submission:
            # 检查作业是否被更新过
            can_resubmit = False
            
            if existing_submission.last_assignment_modified_at is None:
                # 如果没有记录最后修改时间，默认允许重新提交，并更新记录
                can_resubmit = True
            elif assignment.last_modified > existing_submission.last_assignment_modified_at:
                # 如果作业的最后修改时间晚于提交时记录的修改时间，允许重新提交
                can_resubmit = True
                messages.info(request, '作业内容已更新，你可以重新提交。')
            
            if not can_resubmit:
                messages.warning(request, '你已经提交过此作业，且作业内容未更新。不允许重新提交。')
                return redirect('assignments:assignment_detail', pk=pk)
            
            forms = []
            # 读取已有答案
            for question in questions:
                answer = existing_submission.answers.filter(question=question).first()
                forms.append((question, answer))
            
            messages.info(request, '你已经提交过此作业，可以重新提交覆盖之前的答案。')
        else:
            forms = [(q, None) for q in questions]
        
        return render(request, 'assignments/submit_assignment.html', {
            'assignment': assignment,
            'forms': forms
        })

@login_required
def grade_assignment(request, pk):
    """评分作业视图"""
    submission = get_object_or_404(Submission, pk=pk)
    if not is_teacher(request.user) or (request.user != submission.assignment.teacher and not request.user.is_admin()):
        messages.error(request, '您没有权限评分此作业！')
        return redirect('assignments:assignment_detail', pk=submission.assignment.pk)
    
    if request.method == 'POST':
        form = GradeForm(request.POST, instance=submission)
        if form.is_valid():
            submission = form.save()
            messages.success(request, '作业评分成功！')
            return redirect('assignments:assignment_detail', pk=submission.assignment.pk)
    else:
        form = GradeForm(instance=submission)
    return render(request, 'assignments/grade_form.html', {'form': form, 'submission': submission})

class TeacherRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_teacher()

class AssignmentListView(ListView):
    """作业/考试列表视图"""
    model = Assignment
    template_name = 'assignments/assignment_list.html'
    context_object_name = 'assignments'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Assignment.objects.all().order_by('-created_at')
        type_filter = self.request.GET.get('type')
        status_filter = self.request.GET.get('status')
        
        if type_filter and type_filter != 'all':
            queryset = queryset.filter(type=type_filter)
        
        if status_filter and status_filter != 'all':
            if status_filter == 'active':
                queryset = queryset.filter(start_time__lte=timezone.now(), end_time__gte=timezone.now())
            elif status_filter == 'upcoming':
                queryset = queryset.filter(start_time__gt=timezone.now())
            elif status_filter == 'completed':
                queryset = queryset.filter(end_time__lt=timezone.now())
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['user_submissions'] = {
                submission.assignment_id: submission
                for submission in Submission.objects.filter(student=self.request.user)
            }
        return context

class AssignmentDetailView(LoginRequiredMixin, DetailView):
    """作业/考试详情视图"""
    model = Assignment
    template_name = 'assignments/assignment_detail.html'
    context_object_name = 'assignment'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignment = self.get_object()
        
        # 获取当前用户的提交记录
        if self.request.user.is_authenticated:
            context['submission'] = assignment.submissions.filter(student=self.request.user).first()
            
            # 如果有提交记录，获取每个题目的答案
            if context['submission']:
                answers = {}
                for question in assignment.questions.all():
                    answer = context['submission'].answers.filter(question=question).first()
                    if answer:
                        answers[question.id] = answer
                context['answers'] = answers
        
        return context

class AssignmentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """创建作业/考试视图"""
    model = Assignment
    form_class = AssignmentForm
    template_name = 'assignments/assignment_form.html'
    success_url = reverse_lazy('assignments:assignment_list')
    
    def test_func(self):
        return self.request.user.is_teacher()
    
    def form_valid(self, form):
        form.instance.teacher = self.request.user
        messages.success(self.request, '作业/考试创建成功！')
        return super().form_valid(form)

@login_required
def question_create(request, assignment_pk):
    """创建题目视图"""
    assignment = get_object_or_404(Assignment, pk=assignment_pk)
    
    if not request.user.is_teacher():
        messages.error(request, '只有教师可以创建题目！')
        return redirect('assignments:assignment_detail', pk=assignment_pk)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        
        if form.is_valid():
            question = form.save(commit=False)
            question.assignment = assignment
            
            # 设置题目顺序为当前最大值+1
            last_question = Question.objects.filter(assignment=assignment).order_by('-order').first()
            if last_question:
                question.order = last_question.order + 1
            else:
                question.order = 1
                
            question.save()
            
            if question.type in ['single', 'multiple']:
                formset = ChoiceFormSet(request.POST, instance=question)
                if formset.is_valid():
                    formset.save()
                else:
                    messages.error(request, '选项数据无效！')
                    question.delete()
                    return render(request, 'assignments/question_form.html', {
                        'form': form,
                        'formset': formset,
                        'assignment': assignment
                    })
            
            # 更新作业的最后修改时间
            assignment.last_modified = timezone.now()
            assignment.save(update_fields=['last_modified'])
            
            messages.success(request, '题目创建成功！')
            return redirect('assignments:assignment_detail', pk=assignment_pk)
        else:
            messages.error(request, '题目数据无效！')
            formset = ChoiceFormSet(request.POST)
    else:
        form = QuestionForm()
        formset = ChoiceFormSet()
    
    return render(request, 'assignments/question_form.html', {
        'form': form,
        'formset': formset,
        'assignment': assignment
    })

@login_required
def question_update(request, question_pk):
    """更新题目视图"""
    question = get_object_or_404(Question, pk=question_pk)
    original_order = question.order  # 记录原始顺序
    
    if not request.user.is_teacher():
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        
        if form.is_valid():
            question = form.save(commit=False)
            question.order = original_order  # 确保顺序保持不变
            question.save()
            
            if question.type in ['single', 'multiple']:
                formset = ChoiceFormSet(request.POST, instance=question)
                if formset.is_valid():
                    formset.save()
                else:
                    messages.error(request, '选项数据无效！')
                    return render(request, 'assignments/question_form.html', {
                        'form': form,
                        'formset': formset,
                        'question': question,
                        'assignment': question.assignment
                    })
            
            # 更新作业的最后修改时间
            question.assignment.last_modified = timezone.now()
            question.assignment.save(update_fields=['last_modified'])
            
            messages.success(request, '题目更新成功！')
            return redirect('assignments:assignment_detail', pk=question.assignment.pk)
        else:
            messages.error(request, '题目数据无效！')
            if question.type in ['single', 'multiple']:
                formset = ChoiceFormSet(request.POST, instance=question)
            else:
                formset = ChoiceFormSet(instance=question)
    else:
        form = QuestionForm(instance=question)
        formset = ChoiceFormSet(instance=question)
    
    return render(request, 'assignments/question_form.html', {
        'form': form,
        'formset': formset,
        'question': question,
        'assignment': question.assignment
    })

@login_required
def take_exam(request, assignment_pk):
    """参加考试视图"""
    assignment = get_object_or_404(Assignment, pk=assignment_pk)
    
    # 检查是否在考试时间内
    now = timezone.now()
    if not (assignment.start_time <= now <= assignment.end_time):
        messages.error(request, '不在考试时间内！')
        return redirect('assignments:assignment_detail', pk=assignment_pk)
    
    # 检查是否已经提交过
    if Submission.objects.filter(assignment=assignment, student=request.user).exists():
        messages.error(request, '您已经提交过这次考试！')
        return redirect('assignments:assignment_detail', pk=assignment_pk)
    
    if request.method == 'POST':
        with transaction.atomic():
            # 创建提交记录
            submission = Submission.objects.create(
                assignment=assignment,
                student=request.user
            )
            
            # 处理每个题目的答案
            total_score = 0
            for question in assignment.questions.all():
                answer = Answer.objects.create(
                    submission=submission,
                    question=question
                )
                
                if question.type == 'text':
                    # 处理简答题
                    answer.content = request.POST.get(f'question_{question.pk}', '')
                else:
                    # 处理选择题
                    choice_pks = request.POST.getlist(f'question_{question.pk}')
                    if choice_pks:
                        answer.selected_choices.set(choice_pks)
                        # 自动评分
                        score = answer.calculate_score()
                        if score is not None:
                            answer.score = score
                            total_score += score
                
                answer.save()
            
            # 如果所有题目都是选择题，更新总分
            if not assignment.questions.filter(type='text').exists():
                submission.score = total_score
                submission.is_graded = True
                submission.graded_by = request.user
                submission.graded_at = now
                submission.save()
        
        messages.success(request, '考试提交成功！')
        return redirect('assignments:assignment_detail', pk=assignment_pk)
    
    return render(request, 'assignments/take_exam.html', {
        'assignment': assignment
    })

@login_required
def submit_homework(request, assignment_pk):
    """提交作业视图"""
    assignment = get_object_or_404(Assignment, pk=assignment_pk)
    
    # 检查是否在提交时间内
    now = timezone.now()
    if now > assignment.end_time:
        messages.error(request, '已超过提交截止时间！')
        return redirect('assignments:assignment_detail', pk=assignment_pk)
    
    # 获取或创建提交记录
    submission, created = Submission.objects.get_or_create(
        assignment=assignment,
        student=request.user
    )
    
    if request.method == 'POST':
        forms = []
        for question in assignment.questions.all():
            answer, _ = Answer.objects.get_or_create(
                submission=submission,
                question=question
            )
            form = AnswerForm(request.POST, prefix=f'q{question.pk}', instance=answer)
            forms.append((question, form))
        
        if all(form.is_valid() for _, form in forms):
            for question, form in forms:
                form.save()
            
            messages.success(request, '作业提交成功！')
            return redirect('assignments:assignment_detail', pk=assignment_pk)
    else:
        forms = []
        for question in assignment.questions.all():
            answer, _ = Answer.objects.get_or_create(
                submission=submission,
                question=question
            )
            form = AnswerForm(prefix=f'q{question.pk}', instance=answer)
            forms.append((question, form))
    
    return render(request, 'assignments/submit_assignment.html', {
        'assignment': assignment,
        'forms': forms
    })

@login_required
def grade_submission(request, submission_pk):
    """评分视图"""
    submission = get_object_or_404(Submission, pk=submission_pk)
    
    if not request.user.is_teacher() and not request.user.is_superuser:
        messages.error(request, '只有教师可以评分！')
        return redirect('assignments:assignment_detail', pk=submission.assignment.pk)
    
    # 确保所有答案记录都已创建
    questions = submission.assignment.questions.all()
    print(f"准备评分提交ID: {submission.pk}, 总题目数: {questions.count()}")
    
    for question in questions:
        ans, created = Answer.objects.get_or_create(submission=submission, question=question)
        if created:
            print(f"为题目{question.id}创建了新答案记录: {ans.id}")
        else:
            print(f"使用已有答案记录: {ans.id}, 题目: {question.id}, 分数: {ans.score}")
    
    if request.method == 'POST':
        print(f"收到POST请求, 处理评分")
        forms = []
        total_score = 0
        all_answers_scored = True
        
        # 首先处理手动调整选择题评分
        for answer in submission.answers.filter(question__type__in=['single', 'multiple']):
            print(f"检查选择题手动评分: 答案ID={answer.id}")
            override_key = f"override_score_{answer.id}"
            
            if override_key in request.POST:
                manual_score_key = f"manual_score_{answer.id}"
                if manual_score_key in request.POST and request.POST[manual_score_key].strip():
                    try:
                        manual_score = float(request.POST[manual_score_key])
                        # 验证分数在合理范围内
                        if 0 <= manual_score <= float(answer.question.score):
                            answer.score = manual_score
                            answer.save(update_fields=['score'])
                            print(f"  已手动调整选择题分数: 答案ID={answer.id}, 新分数={manual_score}")
                        else:
                            print(f"  手动分数超出范围: {manual_score}, 应在0-{answer.question.score}之间")
                            messages.error(request, f'题目{answer.question.id}的分数必须在0-{answer.question.score}之间')
                    except ValueError:
                        print(f"  无效的分数格式: {request.POST[manual_score_key]}")
                        messages.error(request, f'题目{answer.question.id}的分数格式无效')
        
        # 首先对选择题进行自动评分
        choice_questions = submission.answers.filter(question__type__in=['single', 'multiple'])
        print(f"选择题答案数量: {choice_questions.count()}")
        
        for answer in choice_questions:
            print(f"处理选择题答案ID: {answer.id}, 题目ID: {answer.question.id}, 类型: {answer.question.type}")
            
            # 显示当前选择情况
            selected_ids = [c.id for c in answer.selected_choices.all()]
            print(f"  已选择选项IDs: {selected_ids}, 数量: {len(selected_ids)}")
            
            # 尝试获取正确选项
            correct_choices = answer.question.choices.filter(is_correct=True)
            correct_ids = [c.id for c in correct_choices]
            print(f"  正确选项IDs: {correct_ids}, 数量: {len(correct_ids)}")
            
            # 如果选择题未评分且有选择，尝试自动评分
            if answer.score is None and answer.selected_choices.exists():
                score = answer.calculate_score()
                print(f"  计算得分结果: {score}")
                
                if score is not None:
                    answer.score = score
                    answer.save(update_fields=['score'])
                    print(f"  自动评分选择题成功: 题目{answer.question.id}, 得分{score}")
                else:
                    print(f"  警告: 计算得分为None，可能需要人工评分")
        
        # 获取所有答案再次统计
        for answer in submission.answers.all():
            print(f"处理答案评分统计: ID: {answer.id}, 题目: {answer.question.id}, 类型: {answer.question.type}")
            
            if answer.question.type == 'text':
                # 对简答题进行人工评分
                form = GradeForm(request.POST, prefix=f'a{answer.pk}', instance=answer)
                forms.append((answer, form))
                
                # 检查表单数据
                score_value = request.POST.get(f'a{answer.pk}-score')
                print(f"  简答题表单数据: 分数={score_value}")
                
                if not score_value or score_value.strip() == '':
                    all_answers_scored = False
                    print(f"  简答题{answer.question.id}分数未填写")
            else:
                # 累加选择题分数
                if answer.score is not None:
                    total_score += float(answer.score)
                    print(f"  累加选择题分数: +{answer.score}, 当前总分{total_score}")
                else:
                    all_answers_scored = False
                    print(f"  选择题未评分: ID={answer.id}, 题目={answer.question.id}")
        
        # 处理整体评语
        feedback = request.POST.get('feedback', '').strip()
        if feedback:
            submission.feedback = feedback
            print(f"设置整体评语: {feedback[:50]}...")
        
        # 验证并保存所有表单
        if forms:
            print(f"处理{len(forms)}个简答题表单")
            if all(form.is_valid() for _, form in forms):
                # 保存每个评分表单
                for answer, form in forms:
                    answer = form.save()
                    print(f"保存简答题评分: 题目{answer.question.id}, 分数{answer.score}")
                    if answer.score is not None:
                        total_score += float(answer.score)
                    else:
                        all_answers_scored = False
                
                # 如果所有答案都已评分，更新总分
                if all_answers_scored:
                    submission.score = total_score
                    print(f"所有题目评分完成, 总分: {total_score}")
                    messages.success(request, f'评分完成！总分：{total_score}分')
                else:
                    print(f"部分题目未评分, 不更新总分")
                    messages.warning(request, '部分题目尚未评分，提交总分将在所有题目评分完成后更新。')
                
                submission.save()  # 保存评语和可能的总分
                return redirect('assignments:assignment_detail', pk=submission.assignment.pk)
            else:
                # 如果表单验证失败，显示错误信息
                for _, form in forms:
                    print(f"表单验证失败: {form.errors}")
                    for field, errors in form.errors.items():
                        for error in errors:
                            messages.error(request, f'表单错误: {error}')
        else:
            # 如果没有需要人工评分的表单（全是选择题）
            if all_answers_scored:
                # 所有选择题都已评分，更新总分
                submission.score = total_score
                print(f"全是选择题且已全部评分, 总分: {total_score}")
                messages.success(request, f'评分完成！总分：{total_score}分')
            else:
                print(f"有未评分选择题")
                messages.warning(request, '有未作答的选择题，无法完成评分。')
            
            submission.save()  # 保存评语和可能的总分
            return redirect('assignments:assignment_detail', pk=submission.assignment.pk)
    else:
        # GET请求处理
        print(f"GET请求, 准备评分表单")
        forms = []
        
        # 自动评分所有未评分的选择题
        choice_questions = submission.answers.filter(question__type__in=['single', 'multiple'], score__isnull=True)
        print(f"需要自动评分的选择题数量: {choice_questions.count()}")
        
        for answer in choice_questions:
            print(f"处理选择题自动评分: 答案ID={answer.id}, 题目ID={answer.question.id}")
            
            # 检查已选择的选项
            selected_choices = answer.selected_choices.all()
            selected_ids = [c.id for c in selected_choices]
            print(f"  已选择选项IDs: {selected_ids}, 数量: {len(selected_ids)}")
            
            if selected_choices.exists():
                # 获取正确选项
                correct_choices = answer.question.choices.filter(is_correct=True)
                correct_ids = [c.id for c in correct_choices]
                print(f"  正确选项IDs: {correct_ids}, 数量: {len(correct_ids)}")
                
                # 计算得分
                score = answer.calculate_score()
                print(f"  计算得分结果: {score}")
                
                if score is not None:
                    answer.score = score
                    answer.save()
                    print(f"  自动评分选择题成功: 题目{answer.question.id}, 得分: {score}")
                else:
                    print(f"  选择题无法自动评分: {answer.question.id}")
            else:
                print(f"  选择题未选择任何选项: {answer.question.id}")
        
        # 获取所有需要显示评分表单的答案
        for answer in submission.answers.all():
            print(f"检查答案: 题目{answer.question.id}, 类型{answer.question.type}, 分数{answer.score}")
            if answer.question.type == 'text':
                form = GradeForm(prefix=f'a{answer.pk}', instance=answer)
                forms.append((answer, form))
                print(f"  添加简答题评分表单")
    
    return render(request, 'assignments/grade_submission.html', {
        'submission': submission,
        'forms': forms
    })

@login_required
def submission_list(request, pk):
    """查看作业提交列表视图"""
    assignment = get_object_or_404(Assignment, pk=pk)
    
    if not request.user.is_teacher() and not request.user.is_superuser:
        messages.error(request, '只有教师可以查看提交列表！')
        return redirect('assignments:assignment_detail', pk=pk)
    
    # 获取所有提交记录
    submissions = assignment.submissions.all().order_by('-submitted_at')
    
    # 计算每个提交的评分状态
    for submission in submissions:
        # 检查是否有未评分的简答题
        has_unscored_text = submission.answers.filter(
            question__type='text',
            score__isnull=True
        ).exists()
        
        # 检查是否有未评分的选择题
        has_unscored_choice = submission.answers.filter(
            question__type__in=['single', 'multiple'],
            score__isnull=True
        ).exists()
        
        # 如果有未评分的题目，标记为需要评分
        submission.needs_grading = has_unscored_text or has_unscored_choice
        submission.is_fully_graded = not submission.needs_grading and submission.score is not None
        
        # 添加更详细的评分需求标记
        submission.has_unscored_text = has_unscored_text
        submission.has_unscored_choice = has_unscored_choice
        
        # 如果所有题目都已评分但总分未更新，计算总分
        if not submission.needs_grading and submission.score is None:
            total_score = sum(float(answer.score or 0) for answer in submission.answers.all())
            submission.score = total_score
            submission.save()
    
    # 过滤显示需要评分的提交
    pending_submissions = [sub for sub in submissions if sub.needs_grading or sub.score is None]
    
    return render(request, 'assignments/submission_list.html', {
        'assignment': assignment,
        'submissions': submissions,
        'pending_submissions': pending_submissions
    })

@login_required
def question_edit(request, pk):
    """编辑题目视图"""
    question = get_object_or_404(Question, pk=pk)
    original_order = question.order  # 记录原始顺序
    
    if not request.user.is_teacher():
        messages.error(request, '只有教师可以编辑题目！')
        return redirect('assignments:assignment_detail', pk=question.assignment.pk)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        
        if form.is_valid():
            question = form.save(commit=False)
            question.order = original_order  # 确保顺序保持不变
            question.save()
            
            if question.type in ['single', 'multiple']:
                formset = ChoiceFormSet(request.POST, instance=question)
                if formset.is_valid():
                    formset.save()
                else:
                    messages.error(request, '选项数据无效！')
                    return render(request, 'assignments/question_form.html', {
                        'form': form,
                        'formset': formset,
                        'question': question,
                        'assignment': question.assignment
                    })
            
            messages.success(request, '题目更新成功！')
            return redirect('assignments:assignment_detail', pk=question.assignment.pk)
        else:
            messages.error(request, '题目数据无效！')
            if question.type in ['single', 'multiple']:
                formset = ChoiceFormSet(request.POST, instance=question)
            else:
                formset = None
    else:
        form = QuestionForm(instance=question)
        formset = ChoiceFormSet(instance=question)
    
    return render(request, 'assignments/question_form.html', {
        'form': form,
        'formset': formset,
        'question': question,
        'assignment': question.assignment
    })

@login_required
def question_delete(request, pk):
    """删除题目视图"""
    question = get_object_or_404(Question, pk=pk)
    
    if not request.user.is_teacher():
        messages.error(request, '只有教师可以删除题目！')
        return redirect('assignments:assignment_detail', pk=question.assignment.pk)
    
    if request.method == 'POST':
        try:
            assignment = question.assignment  # 保存关联的作业引用
            question.delete()
            
            # 更新作业的最后修改时间
            assignment.last_modified = timezone.now()
            assignment.save(update_fields=['last_modified'])
            
            messages.success(request, '题目删除成功！')
        except Exception as e:
            messages.error(request, f'删除题目失败：{str(e)}')
        
        return redirect('assignments:assignment_detail', pk=question.assignment.pk)
    
    return render(request, 'assignments/question_confirm_delete.html', {
        'question': question,
        'assignment': question.assignment
    })

@login_required
def reorder_questions(request, assignment_pk):
    """重新排序题目，按照当前顺序重新设置序号（1, 2, 3...）"""
    assignment = get_object_or_404(Assignment, pk=assignment_pk)
    
    if not request.user.is_teacher():
        messages.error(request, '只有教师可以重新排序题目！')
        return redirect('assignments:assignment_detail', pk=assignment_pk)
    
    # 按照当前排序获取所有题目
    questions = assignment.questions.all().order_by('order')
    
    # 重新设置顺序
    for index, question in enumerate(questions, 1):
        question.order = index
        question.save(update_fields=['order'])
    
    messages.success(request, '题目顺序已重置！')
    return redirect('assignments:assignment_detail', pk=assignment_pk)

@login_required
def refresh_grading_status(request, pk):
    """刷新作业待评分状态"""
    assignment = get_object_or_404(Assignment, pk=pk)
    
    if not request.user.is_teacher() and not request.user.is_superuser:
        messages.error(request, '只有教师可以更新评分状态！')
        return redirect('assignments:assignment_detail', pk=pk)
    
    submissions = assignment.submissions.all()
    updated_count = 0
    
    for submission in submissions:
        # 确保所有题目都有答案记录
        created = _ensure_answers_for_submission(submission)
        if created:
            updated_count += 1
        
        # 重新计算评分状态
        needs_update = False
        
        # 检查是否有未评分的题目
        has_unscored = submission.answers.filter(score__isnull=True).exists()
        
        # 如果所有题目都已评分但总分未设置，计算总分
        if not has_unscored and submission.score is None:
            total_score = sum(float(answer.score or 0) for answer in submission.answers.all())
            submission.score = total_score
            needs_update = True
        
        if needs_update:
            submission.save()
            updated_count += 1
    
    messages.success(request, f'评分状态已更新！更新了{updated_count}个提交记录。')
    return redirect('assignments:assignment_detail', pk=pk)

@login_required
def assignment_statistics(request, pk):
    """作业评分统计概览视图"""
    assignment = get_object_or_404(Assignment, pk=pk)
    
    if not request.user.is_teacher() and not request.user.is_superuser:
        messages.error(request, '只有教师可以查看评分统计！')
        return redirect('assignments:assignment_detail', pk=pk)
    
    # 获取已评分的提交
    graded_submissions = Submission.objects.filter(
        assignment=assignment,
        score__isnull=False
    ).select_related('student')
    
    total_submissions = Submission.objects.filter(assignment=assignment).count()
    
    # 估算总学生数（这里应修改为实际学生数量的获取方式）
    # 如果系统中有学生与课程或班级的关联，应该从那里获取
    User = get_user_model()
    total_students = User.objects.filter(role='student').count()
    
    # 计算基本统计数据
    stats = {
        'total_submissions': total_submissions,
        'graded_count': graded_submissions.count(),
        'pending_count': Submission.objects.filter(assignment=assignment, score__isnull=True).count(),
        'not_submitted_count': total_students - total_submissions if total_students > 0 else 0,
        'completion_rate': (total_submissions / total_students * 100) if total_students > 0 else 0,
        'grading_progress': (graded_submissions.count() / total_submissions * 100) if total_submissions > 0 else 0,
    }
    
    # 成绩统计
    scores = []
    student_data = []
    
    for submission in graded_submissions:
        if submission.score is not None:
            scores.append(submission.score)
            student_data.append({
                'student': submission.student,
                'score': submission.score,
                'submitted_at': submission.submitted_at,
                'is_late': submission.submitted_at > assignment.end_time
            })
    
    # 按分数排序学生数据
    student_data.sort(key=lambda x: x['score'], reverse=True)
    
    # 分数区间统计
    if scores:
        stats.update({
            'avg_score': sum(scores) / len(scores),
            'max_score': max(scores) if scores else 0,
            'min_score': min(scores) if scores else 0,
            'pass_count': sum(1 for s in scores if s >= assignment.total_score * 0.6),
            'pass_rate': sum(1 for s in scores if s >= assignment.total_score * 0.6) / len(scores) * 100 if scores else 0,
            'score_distribution': {
                'excellent': sum(1 for s in scores if s >= assignment.total_score * 0.9),
                'good': sum(1 for s in scores if assignment.total_score * 0.8 <= s < assignment.total_score * 0.9),
                'average': sum(1 for s in scores if assignment.total_score * 0.7 <= s < assignment.total_score * 0.8),
                'passing': sum(1 for s in scores if assignment.total_score * 0.6 <= s < assignment.total_score * 0.7),
                'failing': sum(1 for s in scores if s < assignment.total_score * 0.6),
            }
        })
    else:
        stats.update({
            'avg_score': 0,
            'max_score': 0,
            'min_score': 0,
            'pass_count': 0,
            'pass_rate': 0,
            'score_distribution': {
                'excellent': 0,
                'good': 0,
                'average': 0,
                'passing': 0,
                'failing': 0,
            }
        })
    
    # 题目难度分析
    question_stats = []
    for question in assignment.questions.all():
        answers = Answer.objects.filter(
            question=question,
            submission__assignment=assignment,
            score__isnull=False
        )
        
        if answers.exists():
            avg_score = sum(a.score or 0 for a in answers) / answers.count()
            max_score = max(a.score or 0 for a in answers)
            difficulty = 1 - (avg_score / question.score) if question.score > 0 else 0
            
            question_stats.append({
                'question': question,
                'avg_score': avg_score,
                'max_score': max_score,
                'difficulty': difficulty,
                'difficulty_level': '简单' if difficulty < 0.3 else '中等' if difficulty < 0.7 else '困难'
            })
    
    return render(request, 'assignments/assignment_statistics.html', {
        'assignment': assignment,
        'stats': stats,
        'student_data': student_data,
        'question_stats': question_stats
    })

@login_required
def check_pending_text_submissions(request):
    """检查所有已截止作业中的未评分简答题提交"""
    if not request.user.is_teacher() and not request.user.is_superuser:
        messages.error(request, '只有教师可以使用此功能')
        return redirect('assignments:assignment_list')
    
    # 获取当前时间
    now = timezone.now()
    
    # 获取所有已截止的作业
    ended_assignments = Assignment.objects.filter(end_time__lt=now)
    
    # 初始化结果数据
    pending_submissions = []
    
    # 遍历每个已截止的作业
    for assignment in ended_assignments:
        # 获取该作业下所有提交
        submissions = assignment.submissions.all()
        
        # 筛选出包含未评分简答题的提交
        for submission in submissions:
            # 检查是否有未评分的简答题
            has_unscored_text = submission.answers.filter(
                question__type='text',
                score__isnull=True
            ).exists()
            
            if has_unscored_text:
                pending_submissions.append({
                    'assignment': assignment,
                    'submission': submission,
                    'student': submission.student,
                    'submitted_at': submission.submitted_at
                })
    
    return render(request, 'assignments/pending_text_submissions.html', {
        'pending_submissions': pending_submissions
    }) 