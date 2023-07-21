from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from .models import *
from django.views import View
from .forms import *
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.utils.decorators import method_decorator

# Create your views here.

class IndexView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'olapp/index.html')

class InstructorLoginView(View):
    def get(self, request, *args, **kwargs):
        if request.user and request.user.is_authenticated and request.user.is_active and request.user.groups.filter(name='instructors').exists():
                return HttpResponseRedirect(reverse('olapp:instructor_homepage'))
        if request.user and request.user.is_authenticated and request.user.is_active:
            return HttpResponse('You are already logged in. Please logout and try again.')
        form = InstructorLoginForm()
        return render(request, 'olapp/instructor_login.html', {'form': form})
    def post(self, request, *args, **kwargs):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                if user.groups.filter(name='instructors').exists():
                    login(request, user)
                    return HttpResponseRedirect(reverse('olapp:instructor_homepage'))
                else:
                    return HttpResponse('Please login as an instructor or move to the student website')    
            else:
                return HttpResponse('Your account is disabled')
        else:
            return HttpResponse('Login details are incorrect')

class InstructorHomepageView(View):

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        if request.user.groups.filter(name='instructors').exists():
            return render(request, 'olapp/instructor_homepage.html')
        else:
            return HttpResponse('This page is only accessible to an instructor. Please login as an instructor.')

class LogoutView(View):
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        logout(request)
        return HttpResponseRedirect(reverse(('olapp:index')))

class InstructorSignupView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponse('To create a new instructor account, please logout first.')
        form = InstructorSignupForm()
        return render(request, 'olapp/instructor_signup.html', {'form': form})

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponse('To create a new user account, please logout first.')
        form = InstructorSignupForm(request.POST)
        if form.is_valid():
            new_instructor = form.save()
            instructor_group = Group.objects.get(name='instructors')
            new_instructor.groups.add(instructor_group)
            new_instructor.save()
            return HttpResponseRedirect(reverse('olapp:instructor_login'))
        else:
            return HttpResponse('Some error occurred with the signup form. Please try again.')

class CreateQuizView(View):
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        if request.user.groups.filter(name='instructors').exists():
            course_no = kwargs['course_no']
            course = get_object_or_404(Course, pk=course_no)
            instructor = course.instructor
            if request.user.instructor == instructor:
                form = QuizForm()
                context = {
                    'course': course,
                    'form': form,
                }
                return render(request, 'olapp/create_quiz.html', context)
            else :
                return HttpResponse('Please login as the instructor to access this course')
        else :
            return HttpResponse('Please login as the instructor to access this course')
    
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        if request.user.groups.filter(name='instructors').exists():
            course_no = kwargs['course_no']
            course = get_object_or_404(Course, pk=course_no)
            instructor = course.instructor
            if request.user.instructor == instructor:
                form = QuizForm(request.POST)
                if form.is_valid():
                    new_quiz = form.save(commit=False)
                    new_quiz.course = course
                    new_quiz.save()
                    return HttpResponseRedirect(reverse('olapp:create_questions', args=[course.id, new_quiz.id]))
            else :
                return HttpResponse('Please login as the instructor to access this course')
        else :
            return HttpResponse('Please login as the instructor to access this course')
        

@login_required
def create_questions(request, course_no, quiz_no):
    current_question = request.session.get('current_question', None)
    questions = request.session.get('questions', [])
    quiz = get_object_or_404(Quiz, pk=quiz_no)
    course = get_object_or_404(Course, pk=course_no)
    if request.user.groups.filter(name='instructors').exists():
        instructor = course.instructor
        if request.user.instructor == instructor:
            if quiz.course == course:
                pass
            else:
                return HttpResponse('Please access the correct course to add questions to this quiz')
        else :
            return HttpResponse('Please login as the instructor to access this course')
    else :
        return HttpResponse('Please login as the instructor to access this course')
    
    # if current_question == None:
    #     print('None haiiiii')
    
    if request.method == 'POST':
        form = ChoiceForm(request.POST)
        question_form = QuestionForm(request.POST)

        if form.is_valid() and 'add_choice' in request.POST:
            # print('thereeee')
            choice_text = form.cleaned_data['choice_text']
            is_correct = form.cleaned_data['is_correct']

            # Add the choice to the current question's list of choices
            current_question['choices'].append((choice_text, is_correct))

            # Clear the choice form to add the next choice
            form = ChoiceForm()

        elif question_form.is_valid() and 'add_question' in request.POST:
            question_text = question_form.cleaned_data['question_text']
            # print('hereeee')
            # Save the current question and create a new one
            if current_question is not None:
                questions.append(current_question)

            current_question = {'question_text': question_text, 'choices': []}

            # Clear the question form to add the next question
            question_form = QuestionForm()

        elif 'finish_question' in request.POST:
            # Save the current question without creating a new one
            choice_text = form.cleaned_data['choice_text']
            is_correct = form.cleaned_data['is_correct']

            # Add the choice to the current question's list of choices
            if current_question is not None:
                current_question['choices'].append((choice_text, is_correct))
            if current_question is not None:
                questions.append(current_question)
                current_question = None

        elif 'submit_quiz' in request.POST:

            for question_data in questions:
                question = Question.objects.create(quiz=quiz, question_text=question_data['question_text'])

                for choice_data in question_data['choices']:
                    text, is_correct = choice_data
                    Choice.objects.create(question=question, choice_text=text, is_correct=is_correct)
            request.session.pop('current_question', None)
            request.session.pop('questions', None)
            return HttpResponseRedirect(reverse('olapp:instructor_homepage'))

    else:
        form = ChoiceForm()
        question_form = QuestionForm()
    request.session['current_question'] = current_question
    request.session['questions'] = questions
    return render(request, 'olapp/create_questions.html', {'form': form, 'question_form': question_form, 'questions': questions, 'current_question': current_question, 'quiz': quiz, 'course': course})

