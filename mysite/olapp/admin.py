from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Instructor)
admin.site.register(Course)
admin.site.register(VideoLecture)
admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(Student)
admin.site.register(VideoStatus)
admin.site.register(QuizScore)