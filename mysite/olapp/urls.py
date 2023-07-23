from django.urls import path, include
from . import views
from django.views.decorators.csrf import csrf_exempt


app_name = 'olapp'
urlpatterns = [
    path('instructor/login', views.InstructorLoginView.as_view(), name='instructor_login'),
    path('logout', views.LogoutView.as_view(), name='logout'),
    path('instructor/homepage', views.InstructorHomepageView.as_view(), name='instructor_homepage'),
    path('instructor/signup', views.InstructorSignupView.as_view(), name='instructor_signup'),
    path('', views.IndexView.as_view(), name='index'),
    path('instructor/courses/', views.InstructorCourseListView.as_view(), name='instructor_course_list'),
    path('instructor/courses/new/', views.InstructorCourseCreateView.as_view(), name='instructor_course_create'),
    path('instructor/courses/<int:pk>/', views.InstructorCourseUpdateView.as_view(), name='instructor_course_edit'),
    path('instructor/courses/view/<int:pk>/', views.InstructorCourseDetailView.as_view(), name='instructor_course_detail'),
    path('instructor/courses/<int:pk>/add_videolecture/', views.InstructorVideoLectureCreateView.as_view(), name='instructor_add_videolecture'),
    path('instructor/video/<int:pk>/', views.InstructorVideoLectureView.as_view(), name='instructor_videolecture_view'),
    path('instructor/course/<int:course_no>/quiz/create', views.CreateQuizView.as_view(), name='create_quiz'),
    path('instructor/course/<int:course_no>/quiz/<int:quiz_no>/create/questions', views.create_questions, name='create_questions'),
    path('student/login', views.StudentLoginView.as_view(), name='student_login'),
    path('student/homepage', views.StudentHomepageView.as_view(), name='student_homepage'),
    path('student/signup', views.StudentSignupView.as_view(), name='student_signup'),
    path('student/course/<int:course_no>/quiz/<int:quiz_no>/attempt', views.AttemptQuizView.as_view(), name='attempt_quiz'),
    path('student/course/<int:course_no>/quiz/<int:quiz_no>/score', views.QuizScoreView.as_view(), name='quiz_score'),
    path('student/course/search', views.SearchCourseView.as_view(), name='search_course'),
    path('instructor/quiz/<int:pk>/', views.InstructorQuizDetailView.as_view(), name='instructor_quiz_detail'),
    path('pay/', views.pay, name='pay'),
    path('student/course_brief/<int:pk>/', views.StudentCourseBriefDetailView.as_view(), name='student_course_brief_detail'),
    path('student/course/view/<int:pk>/', views.StudentCourseDetailView.as_view(), name='student_course_detail'),
    path('course/<int:pk>/payment/', views.CoursePaymentView.as_view(), name='course_payment'),
    path('course/<str:pk>/payment_done/', views.PaymentDoneView.as_view(), name='payment_done'),
    path('course/<int:pk>/payment_cancelled/', views.PaymentCancelledView.as_view(), name='payment_cancelled'),
    path('paypal/', include('paypal.standard.ipn.urls')),
    path('student/video/<int:pk>/', views.StudentVideoLectureView.as_view(), name='student_videolecture_view'),
    path('buy_membership/', views.BuyMembershipView.as_view(), name='buy_membership'),
    path('membership_payment_done/', views.MembershipPaymentDoneView.as_view(), name='membership_payment_done'),
    path('membership_payment_cancelled/', views.MembershipPaymentCancelledView.as_view(), name='membership_payment_cancelled'),

]