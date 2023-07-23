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
from django.db.models import Q

# Create your views here.

class IndexView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'olapp/index.html')

class StudentLoginView(View):
    def get(self, request, *args, **kwargs):
        if request.user and request.user.is_authenticated and request.user.is_active and request.user.groups.filter(name='students').exists():
                return HttpResponseRedirect(reverse('olapp:student_homepage'))
        if request.user and request.user.is_authenticated and request.user.is_active:
            return HttpResponse('Please logout and try logging in as a student.')
        form = StudentLoginForm()
        return render(request, 'olapp/student_login.html', {'form': form})
    def post(self, request, *args, **kwargs):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                if user.groups.filter(name='students').exists():
                    login(request, user)
                    return HttpResponseRedirect(reverse('olapp:student_homepage'))
                else:
                    return HttpResponse('Please login as a student or move to the instructor website')    
            else:
                return HttpResponse('Your account is disabled')
        else:
            return HttpResponse('Login details are incorrect')

class InstructorLoginView(View):
    def get(self, request, *args, **kwargs):
        if request.user and request.user.is_authenticated and request.user.is_active and request.user.groups.filter(name='instructors').exists():
                return HttpResponseRedirect(reverse('olapp:instructor_homepage'))
        if request.user and request.user.is_authenticated and request.user.is_active:
            return HttpResponse('Please logout and try logging in as an instructor.')
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

class StudentHomepageView(View):

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        if request.user.groups.filter(name='students').exists():
            context = {
                'student': request.user.student,
            }
            return render(request, 'olapp/student_homepage.html', context)
        else:
            return HttpResponse('This page is only accessible to a student. Please login as a student.')

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
            return render(request, 'olapp/instructor_signup.html', {'form': form})

class StudentSignupView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponse('To create a new student account, please logout first.')
        form = StudentSignupForm()
        return render(request, 'olapp/student_signup.html', {'form': form})

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponse('To create a new student account, please logout first.')
        form = StudentSignupForm(request.POST)
        if form.is_valid():
            new_student = form.save()
            student_group = Group.objects.get(name='students')
            new_student.groups.add(student_group)
            new_student.save()
            return HttpResponseRedirect(reverse('olapp:student_login'))
        else:
            return render(request, 'olapp/student_signup.html', {'form': form})

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



class AttemptQuizView(View):
    def calculate_score(self, user_choices):
        correct_answers = 0
        total_answers = 0
        for question_id, choice_ids in user_choices.items():
            total_answers+=1
            question = Question.objects.get(pk=question_id)
            # print(question)
            correct_choice_ids = list(
                Choice.objects.filter(question=question, is_correct=True).values_list('id', flat=True)
            )
            # print(correct_choice_ids)
            # print('******')
            # print(choice_ids)
            user_choice_ids = [int(choice_id) for choice_id in choice_ids]
            if set(user_choice_ids) == set(correct_choice_ids):
                correct_answers += 1
        if total_answers == 0:
            return 0
        return (correct_answers * 100) // total_answers

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        if not(request.user.groups.filter(name='students').exists()):
            return HttpResponse('Please logout and login as the student to access the quiz')
        
        quiz_no = kwargs['quiz_no']
        course_no = kwargs['course_no']
        quiz = get_object_or_404(Quiz, pk=quiz_no)
        course = get_object_or_404(Course, pk=course_no)
        student = request.user.student
        student_courses = student.courses.all()
        if student.membership == 'S' and not(course in student_courses):
            return HttpResponse('Please enroll in the course and then retry')
        if not(quiz.course == course):
            return HttpResponse('No such quiz found for this course')
        if QuizScore.objects.filter(quiz=quiz).filter(student=student).exists():
            return HttpResponseRedirect(reverse('olapp:quiz_score', args=[course_no, quiz_no]))
        questions = quiz.question_set.all()
        form = QuizAttemptForm(questions)
        context = {
            'form': form,
            'quiz': quiz,
            'course': course,
        }
        new_attempt = QuizScore()
        new_attempt.quiz = quiz
        new_attempt.student = student
        new_attempt.score = 0
        new_attempt.save()
        return render(request, 'olapp/attempt_quiz.html', context)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        if not(request.user.groups.filter(name='students').exists()):
            return HttpResponse('Please logout and login as the student to access the quiz')
        quiz_no = kwargs['quiz_no']
        course_no = kwargs['course_no']
        quiz = get_object_or_404(Quiz, pk=quiz_no)
        course = get_object_or_404(Course, pk=course_no)
        student = request.user.student
        student_courses = student.courses.all()
        if student.membership == 'S' and not(course in student_courses):
            return HttpResponse('Please enroll in the course and then retry')
        if not(quiz.course == course):
            return HttpResponse('No such quiz found for this course')
        if QuizScore.objects.filter(quiz=quiz).filter(student=student).exists():
            attempted_quiz = QuizScore.objects.filter(quiz=quiz).filter(student=student)[0]
            if attempted_quiz.graded:
                return HttpResponseRedirect(reverse('olapp:quiz_score', args=[course_no, quiz_no]))
            questions = quiz.question_set.all()
            form = QuizAttemptForm(questions, request.POST)
            attempted_quiz.graded = True
            attempted_quiz.score = 0
            if form.is_valid():
                calculated_score = 0
                # Calculate the score
                user_choices = {key.split('_')[1]: value for key, value in form.cleaned_data.items()}
                print(user_choices)
                calculated_score = self.calculate_score(user_choices)
                attempted_quiz.score = calculated_score
            attempted_quiz.save()
            return HttpResponseRedirect(reverse('olapp:quiz_score', args=[course_no, quiz_no]))
        else:
            return HttpResponse('Please attempt the quiz first')

class QuizScoreView(View):
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        if not(request.user.groups.filter(name='students').exists()):
            return HttpResponse('Please logout and login as the student to access the quiz')
        quiz_no = kwargs['quiz_no']
        course_no = kwargs['course_no']
        quiz = get_object_or_404(Quiz, pk=quiz_no)
        course = get_object_or_404(Course, pk=course_no)
        student = request.user.student
        student_courses = student.courses.all()
        if student.membership == 'S' and not(course in student_courses):
            return HttpResponse('Please enroll in the course and then retry')
        if not(quiz.course == course):
            return HttpResponse('No such quiz found for this course')
        if QuizScore.objects.filter(quiz=quiz).filter(student=student).exists():
            quizscore = QuizScore.objects.filter(quiz=quiz).filter(student=student)[0]
            context = {
                'quiz_title': quizscore.quiz.title,
                'score': quizscore.score,
            }
            return render(request, 'olapp/quiz_score.html', context)
        return HttpResponse('Please attempt the quiz first to display your grade')

class SearchCourseView(View):
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        if not(request.user.groups.filter(name='students').exists()):
            return HttpResponse('Please logout and login as the student to access the search page')
        form = CourseSearchForm(request.GET)
        courses = Course.objects.all()
        # query = request.GET.get('q')
        if form.is_valid():
            # Perform the search using Q objects to filter the courses
            query = form.cleaned_data.get('search_query')
            if query:
                print('here')
                courses = courses.filter(
                    Q(name__icontains=query) | 
                    Q(description__icontains=query) | 
                    Q(instructor__first_name__icontains=query) | 
                    Q(instructor__last_name__icontains=query)
                )
            print(courses)
            print(len(courses))
            if len(courses) > 0:
                return render(request, 'olapp/course_search.html', {'form': form, 'courses': courses})
            return render(request, 'olapp/course_search.html', {'form': form, 'msg': 'No courses found.'})
        return render(request, 'olapp/course_search.html', {'form': form})