from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm
from .models import Course
# from .fields import BinaryFileField


class InstructorLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password'})
    )

class InstructorSignupForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Instructor
        fields = ('username', 'password1', 'password2', 'first_name', 'last_name', 'description')

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'description', 'price']  # Include all your fields here


class VideoLectureForm(forms.ModelForm):
    video_file = forms.FileField() 
    class Meta:
        model = VideoLecture
        fields = ['order', 'title', 'description']  # video is not included here
         # this is a non-model field to handle file upload

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'prerequisite']

class ChoiceForm(forms.Form):
    choice_text = forms.CharField(max_length=200)
    is_correct = forms.BooleanField(required=False)

class QuestionForm(forms.Form):
    question_text = forms.CharField(max_length=200)
