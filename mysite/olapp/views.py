from django.shortcuts import render, get_object_or_404
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
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.contrib import messages
from django.http import StreamingHttpResponse, HttpResponseForbidden


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


class InstructorCourseDetailView(DetailView):
    model = Course
    template_name = 'olapp/instructor_course_detail.html'


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

