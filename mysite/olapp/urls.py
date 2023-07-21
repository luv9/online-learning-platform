from django.urls import path
from . import views

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
]
