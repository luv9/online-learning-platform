from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm

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

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'prerequisite']

class ChoiceForm(forms.Form):
    choice_text = forms.CharField(max_length=200)
    is_correct = forms.BooleanField(required=False)

class QuestionForm(forms.Form):
    question_text = forms.CharField(max_length=200)
