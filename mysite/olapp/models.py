from django.db import models
from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Instructor(User):
    description = models.TextField()
    class Meta:
        verbose_name = "Instructor"
        verbose_name_plural = "Instructors"


class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    price = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


class VideoLecture(models.Model):
    video = models.BinaryField()
    order =  models.PositiveIntegerField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    class Meta:
        ordering=['order']

class Quiz(models.Model):
    prequisite = models.TextField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question_text = models.CharField(max_length=200)
    def __str__(self) -> str:
        return self.question_text

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    def __str__(self) -> str:
        return self.choice_text

class Student(User):
    courses = models.ManyToManyField(Course)
    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"

class VideoStatus(models.Model):
    video = models.ForeignKey(VideoLecture, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    STATUS_CHOICES = [
        ('W', 'Watched'),
        ('N', 'Not Watched')
    ]
    status = models.CharField(choices=STATUS_CHOICES, default='N', max_length=1)

class QuizScore(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()
