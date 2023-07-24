from django.shortcuts import render, get_object_or_404, redirect
import base64
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Course
from .forms import CourseForm
from django.http import HttpResponse, HttpResponseRedirect
from .models import *
from django.views import View
from .forms import *
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.http import HttpResponse
from django.template.loader import get_template
from weasyprint import HTML
from datetime import datetime
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import StreamingHttpResponse, HttpResponseForbidden
from django.db.models import Q
from paypal.standard.forms import PayPalPaymentsForm
from django.urls import reverse
from django.conf import settings
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from paypal.standard.ipn.signals import valid_ipn_received
from django.dispatch import receiver
from paypal.standard.ipn.models import PayPalIPN
from django.urls import reverse

class InstructorCourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'olapp/instructor_course_list.html'
    context_object_name = 'courses'

    def get_queryset(self):
        return Course.objects.filter(instructor=self.request.user)


class InstructorCourseCreateView(LoginRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'olapp/instructor_course_form.html'
    success_url = reverse_lazy('olapp:instructor_course_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.groups.filter(name='instructors').exists():
            messages.error(request, "You must be an instructor to create a course.")
            return redirect('olapp:instructor_course_list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.instructor = self.request.user.instructor
        return super().form_valid(form)


class InstructorCourseUpdateView(LoginRequiredMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'olapp/instructor_course_form.html'
    success_url = reverse_lazy('olapp:instructor_course_list')

    def get_object(self, queryset=None):
        """Retrieve the course, making sure it's owned by the current user."""
        course = super().get_object(queryset)
        if not course.instructor == self.request.user.instructor:
            raise Http404("This course does not exist or you do not have permission to edit it.")
        return course

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
            form = InstructorLoginForm(request.POST)
            return render(request, 'olapp/instructor_login.html', {'form': form, 'msg': 'Login credentials are incorrect.'})
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
                'courses': Course.objects.all(),
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


class InstructorCourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'olapp/instructor_course_detail.html'

    def get_object(self, queryset=None):
        """ Retrieve the course only if the logged in user is the instructor """
        obj = super().get_object(queryset=queryset)

        if not obj.instructor == self.request.user.instructor:
            messages.error(self.request, 'You do not have permission to view this course.')
            return redirect('olapp:instructor_course_list')  # redirect to an appropriate URL

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        students = Student.objects.filter(courses=course)
        student_details = []

        for student in students:
            # Fetch all video lectures and quizzes for the course
            video_lectures = VideoLecture.objects.filter(course=course)
            quizzes = Quiz.objects.filter(course=course)

            # Check if all videos are watched
            all_videos_watched = all(VideoStatus.objects.filter(student=student, video=video, status='W').exists() for video in video_lectures)

            # Fetch quiz scores
            quiz_scores = QuizScore.objects.filter(student=student, quiz__in=quizzes)
            average_score = sum([score.score for score in quiz_scores]) / len(quiz_scores) if quiz_scores else 0

            # Check if all quizzes are completed and score is over 50%
            all_quizzes_completed = all(QuizScore.objects.filter(student=student, quiz=quiz).exists() for quiz in quizzes)
            pass_score = average_score >= 50

            student_details.append({
                'student': student,
                'all_videos_watched': all_videos_watched,
                'all_quizzes_completed': all_quizzes_completed,
                'pass_score': pass_score,
                'course_completed': all_videos_watched and all_quizzes_completed and pass_score,
            })

        context['student_details'] = student_details
        return context


class InstructorVideoLectureCreateView(View):
    def get(self, request, *args, **kwargs):
        form = VideoLectureForm()
        return render(request, 'olapp/instructor_videolecture_form.html', {'form': form})
    

    def post(self, request, *args, **kwargs):
        form = VideoLectureForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.cleaned_data['video_file']
            video_data = video.read()

            # assuming the course id is being passed as a URL parameter
            course_id = self.kwargs['pk']
            course = Course.objects.get(id=course_id)

            # create a new VideoLecture instance with this data
            a = VideoLecture.objects.create(
                video=video_data,
                order=form.cleaned_data['order'],
                title=form.cleaned_data['title'],
                description=form.cleaned_data['description'],
                course=course  # link the VideoLecture to the course
            )

            # redirect to the course detail page after saving
            return redirect('olapp:instructor_course_detail', pk=course_id)
        
        return render(request, 'olapp/instructor_add_video.html', {'form': form})
    

class InstructorVideoStreamView(View):
    def get(self, request, *args, **kwargs):
        videolecture = get_object_or_404(VideoLecture, pk=kwargs['pk'])

        # Check if the instructor has access to the course
        course = videolecture.course
        if course.instructor != request.user.instructor:
            return HttpResponseForbidden('You do not have access to this course.')

        # Create the HttpResponse with the binary data and the appropriate content type
        response = HttpResponse(videolecture.video, content_type='video/mp4')
        return response

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
            return HttpResponseRedirect(reverse('olapp:instructor_course_detail', args=[course_no]))

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
                'course_no': course.id,
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

class InstructorVideoLectureView(View):
    def get(self, request, *args, **kwargs):
        videolecture = get_object_or_404(VideoLecture, pk=kwargs['pk'])

        # Check if the instructor has access to the course
        course = videolecture.course
        if course.instructor != request.user.instructor:
            return HttpResponseForbidden('You do not have access to this course.')

        # Encode the binary data to base64
        video_b64 = base64.b64encode(videolecture.video).decode('utf-8')

        context = {
            'video_data': video_b64,
            'videolecture': videolecture,
        }

        return render(request, 'olapp/instructor_videolecture_detail.html', context)
    
class InstructorQuizDetailView(View):
    def get(self, request, *args, **kwargs):
        quiz_id = self.kwargs['pk']
        quiz = get_object_or_404(Quiz, pk=quiz_id)
        questions = Question.objects.filter(quiz=quiz)
        
        context = {
            'quiz': quiz,
            'questions': questions,
            'course_no': quiz.course.id,
        }
        return render(request, 'olapp/instructor_quiz_detail.html', context)
    
def pay(request):
    host = "https://9b2f-142-116-120-106.ngrok-free.app"  # replace with your ngrok url

    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": "10.00",  # amount to be paid
        "item_name": "name of the asdasd",
        "invoice": "unique-invoice-id10",
        "notify_url": host + reverse('paypal-ipn'),
        "return_url": host + reverse('olapp:payment_done'),
        "cancel_return": host + reverse('olapp:payment_cancelled'),
    }

    form = PayPalPaymentsForm(initial=paypal_dict)
    return render(request, "payment/pay.html", {"form": form})

def payment_done(request):
    return render(request, "payment/payment_done.html")

def payment_cancelled(request):
    return render(request, "payment/payment_cancelled.html")


class StudentCourseBriefDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'olapp/student_course_detail_before_purchase.html'


class StudentCourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'olapp/student_course_detail.html'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)

        if not obj.id in self.request.user.student.courses.values_list('id', flat=True):
            messages.error(self.request, 'You do not have permission to view this course.')
            return redirect('olapp:student_homepage')  # redirect to an appropriate URL

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()

        # Retrieve the video statuses
        video_statuses = VideoStatus.objects.filter(student=self.request.user.student,
                                                    video__course=course)

        # Check if all videos have been watched
        all_videos_watched = all([status.status == 'W' for status in video_statuses])

        # Retrieve the quiz scores
        quiz_scores = QuizScore.objects.filter(student=self.request.user.student,
                                               quiz__course=course)

        # Convert quiz scores to dictionary
        quiz_scores_dict = {score.quiz.id: score.score for score in quiz_scores}

        attempted_quiz_ids = quiz_scores_dict.keys()

        # Check if average quiz score is more than 50%
        average_quiz_score = sum(quiz_scores_dict.values()) / len(quiz_scores_dict) if quiz_scores_dict else 0
        passed_quizzes = average_quiz_score > 50

        context['video_statuses'] = video_statuses
        context['quiz_scores'] = quiz_scores_dict
        context['attempted_quiz_ids'] = attempted_quiz_ids
        context['all_videos_watched'] = all_videos_watched
        context['passed_quizzes'] = passed_quizzes

        return context


class CoursePaymentView(LoginRequiredMixin, View):
    # def dispatch(self, request, *args, **kwargs):
    #     if not request.user.groups.filter(name='students').exists():
    #         messages.error(request, "You must be an instructor to create a course.")
    #         return redirect('olapp:search_course')
    #     return super().dispatch(request, *args, **kwargs)
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        course = Course.objects.get(pk=self.kwargs['pk'])
        student = Student.objects.get(id=request.user.student.id)

        # check if the student is a gold member
        if student.membership == 'G':
            # if they are, add the course to their account and redirect to the course detail page
            student.courses.add(course)
            return redirect('olapp:student_course_detail', pk=course.id)

        # if they are not, continue with the PayPal form creation process
        else:
            host = "https://9b2f-142-116-120-106.ngrok-free.app"

            paypal_dict = {
                'business': settings.PAYPAL_RECEIVER_EMAIL,
                'amount': course.price,
                'item_name': course.name,
                'invoice': str(course.id)+"_"+str(student.id),
                'notify_url': '{}{}'.format(host, reverse('olapp:paypal-ipn')),
                'return_url': '{}{}'.format(host, reverse('olapp:payment_done',kwargs={'pk': str(course.id)+"_"+str(student.id)})),
                'cancel_return': '{}{}'.format(host, reverse('olapp:payment_cancelled', kwargs={'pk': course.id})),
            }

            form = PayPalPaymentsForm(initial=paypal_dict)
            context = {"form": form, "course": course}
            return render(request, 'payment/payment.html', context)
        


@method_decorator(csrf_exempt, name='dispatch')
class PaymentDoneView(View):
    def get(self, request, *args, **kwargs):
        # retrieve the transaction
        print(kwargs)
        txn = get_object_or_404(PayPalIPN, invoice=kwargs['pk'])


        # make sure the transaction was successful
        if txn.payment_status == "Completed":
            # retrieve the user
            student = Student.objects.get(id=request.user.student.id)

            # retrieve the course
            id =txn.invoice.split("_")[0]
            course = Course.objects.get(id=id)

            # add the course to the student
            student.courses.add(course)
            student.save()

            # redirect to the course details page
            return redirect(reverse('olapp:student_course_detail', kwargs={'pk': course.id}))
        else:
            # handle unsuccessful payment
            return render(request, 'payment/payment_unsuccessful.html')


# receiver function to listen to valid payment notifications from PayPal
@receiver(valid_ipn_received)
def payment_notification(sender, **kwargs):
    ipn_obj = sender

    if ipn_obj.payment_status == 'Completed':
        # payment was successful
        print(f'payment for invoice {ipn_obj.invoice} was successful.')

    else:
        # payment did not go through
        print('payment did not go through')


class PaymentCancelledView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'olapp/payment_cancelled.html')
    

class StudentVideoLectureView(View):
    def get(self, request, *args, **kwargs):
        videolecture = get_object_or_404(VideoLecture, pk=kwargs['pk'])

        # Check if the student has access to the course
        course = videolecture.course
        if not course.id in self.request.user.student.courses.values_list('id', flat=True):
            return HttpResponseForbidden('You do not have access to this course.')

        # Set video status to 'Watched'
        video_status, created = VideoStatus.objects.get_or_create(
            video=videolecture,
            student=self.request.user.student,
            defaults={'status': 'N'}
        )
        video_status.status = 'W'
        video_status.save()

        # Encode the binary data to base64
        video_b64 = base64.b64encode(videolecture.video).decode('utf-8')

        context = {
            'video_data': video_b64,
            'videolecture': videolecture,
        }

        return render(request, 'olapp/student_videolecture_detail.html', context)


class MembershipPaymentDoneView(View):
    def get(self, request, *args, **kwargs):
        # retrieve the transaction
        txn = get_object_or_404(PayPalIPN, invoice='G_'+str(request.user.student.id))

        # make sure the transaction was successful
        if txn.payment_status == "Completed":
            # upgrade the user's membership to Gold
            student = Student.objects.get(id=request.user.student.id)
            student.membership = 'G'
            student.save()

            # redirect to the student's homepage
            return redirect('olapp:student_homepage')
        else:
            # handle unsuccessful payment
            return render(request, 'payment/payment_unsuccessful.html')


class BuyMembershipView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # retrieve the student
        student = Student.objects.get(id=request.user.student.id)

        # Check if the student is already a Gold member
        if student.membership == 'G':
            messages.info(request, 'You are already a Gold member.')
            return redirect('olapp:student_homepage')

        # Define a fixed price for the Gold membership
        gold_membership_price = 100  # adjust this as necessary

        # Create PayPal form for Gold membership purchase
        host = "https://9b2f-142-116-120-106.ngrok-free.app"
        paypal_dict = {
            'business': settings.PAYPAL_RECEIVER_EMAIL,
            'amount': gold_membership_price,
            'item_name': 'Gold Membership',
            'invoice': 'G_' + str(student.id),
            'notify_url': '{}{}'.format(host, reverse('olapp:paypal-ipn')),
            'return_url': '{}{}'.format(host, reverse('olapp:membership_payment_done')),
            'cancel_return': '{}{}'.format(host, reverse('olapp:membership_payment_cancelled')),
        }

        form = PayPalPaymentsForm(initial=paypal_dict)
        context = {"form": form}
        return render(request, 'payment/payment.html', context)


class MembershipPaymentCancelledView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'olapp/membership_payment_cancelled.html')


def download_certificate(request, course_no):
    # Fetch course details
    course = get_object_or_404(Course, pk=course_no)
    
    # Fetch student details
    student = request.user.student

    # Fetch average score
    quiz_scores = QuizScore.objects.filter(student=student, quiz__course=course)
    average_score = sum([score.score for score in quiz_scores]) / len(quiz_scores) if quiz_scores else 0

    # Render certificate HTML with context data
    template = get_template('olapp/certificate.html')
    html = template.render({
        'course': course,
        'student': student,
        'date': datetime.now().strftime('%d %B, %Y'),
        'average_score': round(average_score, 2),
    })

    # Convert HTML to PDF with WeasyPrint
    pdf = HTML(string=html).write_pdf()

    # Create response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{course.name}_certificate.pdf"'

    return response