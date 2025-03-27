from django.urls import path
from . import views

app_name = 'assignments'

urlpatterns = [
    # 作业/考试相关
    path('', views.AssignmentListView.as_view(), name='assignment_list'),
    path('create/', views.AssignmentCreateView.as_view(), name='assignment_create'),
    path('<int:pk>/', views.assignment_detail, name='assignment_detail'),
    path('<int:pk>/update/', views.AssignmentUpdateView.as_view(), name='assignment_update'),
    path('<int:pk>/delete/', views.AssignmentDeleteView.as_view(), name='assignment_delete'),
    path('<int:pk>/submit/', views.submit_assignment, name='submit_assignment'),
    path('<int:assignment_pk>/submit_homework/', views.submit_homework, name='submit_homework'),
    path('<int:pk>/grade/', views.grade_assignment, name='grade_assignment'),
    path('<int:pk>/submissions/', views.submission_list, name='submission_list'),
    path('<int:pk>/refresh_grading/', views.refresh_grading_status, name='refresh_grading_status'),
    path('<int:pk>/statistics/', views.assignment_statistics, name='assignment_statistics'),
    path('pending-text-submissions/', views.check_pending_text_submissions, name='pending_text_submissions'),
    
    # 题目相关
    path('<int:assignment_pk>/question/create/', views.question_create, name='question_create'),
    path('question/<int:pk>/edit/', views.question_edit, name='question_edit'),
    path('question/<int:pk>/delete/', views.question_delete, name='question_delete'),
    path('question/<int:question_pk>/update/', views.question_update, name='question_update'),
    path('<int:assignment_pk>/take/', views.take_exam, name='take_exam'),
    path('submission/<int:submission_pk>/grade/', views.grade_submission, name='grade_submission'),
    path('<int:assignment_pk>/reorder/', views.reorder_questions, name='reorder_questions'),
] 