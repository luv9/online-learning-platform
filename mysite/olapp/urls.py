from django.urls import path
from . import views

app_name = 'olapp'
urlpatterns = [
    # path('', views.IndexView, name='homepage'),
    # path('<int:cartype_no>', views.CarDetailView.as_view(), name='cardetail'),
    path('instructor/login', views.InstructorLoginView.as_view(), name='instructor_login'),
    path('logout', views.LogoutView.as_view(), name='logout'),
    path('instructor/homepage', views.InstructorHomepageView.as_view(), name='instructor_homepage'),
    path('instructor/signup', views.InstructorSignupView.as_view(), name='instructor_signup'),
    path('', views.IndexView.as_view(), name='index'),
]