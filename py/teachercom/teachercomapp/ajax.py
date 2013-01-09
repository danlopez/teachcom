from django.db import models
from django.core.context_processors import csrf
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from teachercomapp.models import Message, Teacher, Student
from django.core import serializers
from django.utils import simplejson


# @ensure_csrf_cookie
def delete_message(request):
    response={}
    if request.is_ajax():
        if request.method=="POST":
            # check if message exists
            message_id = request.POST['message_id']
            teacher = Teacher.objects.get(user=request.user)
            message = Message.objects.get(id = message_id)
            if message.teacher == teacher: # check is user is owner of message
                message.delete()
                response['error'] = "ok"
            else:
                response['error'] = "failed"
        else: 
            response['error'] = "not a post request"
    else:
        response['error'] = "Not an ajax request"
    json_response=simplejson.dumps(response)
    return HttpResponse(json_response)


# def delete_student(request):
#     response={}
#     if request.is_ajax():
#         if request.method=="POST":
#             # check if student exists
#             student_id = request.POST['student_id']
#             teacher = Teacher.objects.get(user=request.user)
#             student = Student.objects.get(id = student_id)
#             if teacher in student.teachers: # check is user is owner of student
#                 student.delete()
#                 response['error'] = "ok"
#             else:
#                 response['error'] = "failed"
#         else: 
#             response['error'] = "not a post request"
#     else:
#         response['error'] = "Not an ajax request"
#     json_response=simplejson.dumps(response)
#     return HttpResponse(json_response)
