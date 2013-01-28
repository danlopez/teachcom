# Create your views here.
from django.core.context_processors import csrf
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from teachercomapp.models import Student, Message, Event, Teacher
from teachercomapp.forms import MessageForm, StudentForm
import datetime
import csv
import StringIO
from twilio import twiml
from django import template
from django.db.models import Q
from twilio.rest import TwilioRestClient
from teachercom.settings import *


@cache_page(1)
def index(request):
    data = {
        'user': request.user,
    }

    return render_to_response('index.html', data)

def send(request):
    if request.method == 'GET':
        teacher = Teacher.objects.get(user=request.user)
        data = {
            'students': Student.objects.filter(teachers=teacher).order_by('first_name'),
            'messages': Message.objects.filter(teacher=teacher).order_by('label'),
            'user': request.user,
        }
        data.update(csrf(request))
        return render_to_response('send.html', data)
    else:
        data = {
            'user': request.user,
        }
        message = Message.objects.get(pk=request.POST['message'])
        for student_id in request.POST.getlist('students'):
            student = Student.objects.get(pk=student_id)
            if student.sms_notification_ind:
                send_message(student, message, 1)
            if student.call_notification_ind:
                send_message(student, message, 2)
            if student.email_notification_ind:
                send_message(student, message, 3)
        return render_to_response('sent.html', data)

def list_students(request):
    teacher = Teacher.objects.get(user=request.user)
    data = {
        'students': Student.objects.filter(teachers=teacher).order_by('first_name'),
        'user': request.user,
    }
    return render_to_response('list_students.html', data)
    
def handle_csv(request):
    """ Note: not a whole lot of error detection / correction
        going on here, if a bad csv comes in, it'll 500 """
    if request.method == 'GET':
        data = {
            'user': request.user,
        }
        data.update(csrf(request))
        return render_to_response('csv.html', data)
    else:
        data = {
            'user': request.user,
        }

        f = request.FILES['csv']
        contents = f.read().replace('\r\n', '\n').replace('\r', '\n')

        fp = StringIO.StringIO(contents)

        # Check if we need to skip the first line
        if request.POST['skip_first_line'] == 'on':
            next(fp)

        teacher = Teacher.objects.get(user=request.user)

        reader = csv.reader(fp)
        for row in reader:
            student = Student(
                student_id = row[0].strip(),
                first_name = row[1].strip(),
                last_name = row[2].strip(),
                phone_number = row[3].strip(),
                email = row[4].strip(),
                sms_notification_ind = (row[5].strip().lower() == 'true'),
                call_notification_ind = (row[6].strip().lower() == 'true'),
                email_notification_ind = (row[7].strip().lower() == 'true'),
            )
            student.save()
            student.teachers.add(teacher)
            student.save()
        return render_to_response('csv-saved.html', data)

def call_log(request):
    teacher = Teacher.objects.get(user = request.user)
    data = {
            'events': Event.objects.filter(message__in = Message.objects.filter(teacher = teacher)),
            'user': request.user,
        }
    return render_to_response('call_log.html', data)        

def edit_student(request, student_id):
    student = Student.objects.get(id = student_id)
    if request.method == 'GET':
        data = {
                'form' : StudentForm (instance = student),
                'user' : request.user,
        }
        data.update(csrf(request))
        return render_to_response('standard_form.html', data)
    elif request.method =='POST':
        student_form = StudentForm(request.POST, instance = student)
        data = {
                'form' : student_form,
                'user' : request.user,
        } 
        data.update(csrf(request))
        if student_form.is_valid():
            student_form.save()
            return redirect('list_students')
        else:
            return render_to_response('standard_form.html', data) 

def new_student(request):
    if request.method == 'GET':
        data = {
                'form' : StudentForm(),
                'user' : request.user,
        }
        data.update(csrf(request))
        return render_to_response('standard_form.html', data)
    elif request.method =='POST':
        student_form = StudentForm(request.POST)
        data = {
                'form' : student_form,
                'user' : request.user,
        } 
        data.update(csrf(request))
        if student_form.is_valid():
            student = student_form.save(commit=False)
            student.save()
            student.teachers.add(Teacher.objects.get(user=request.user))
            student.save()
            return redirect('list_students')
        else:
            return render_to_response('standard_form.html', data) 

def edit_message(request, message_id):
    message = Message.objects.get(id = message_id)
    if request.method=='GET':
        data = {
                'form' : MessageForm (instance = message),
                'user' : request.user,
        }
        data.update(csrf(request))
        return render_to_response('standard_form.html', data)
    elif request.method=='POST':
        message_form = MessageForm(request.POST, instance = message)
        data = {
                'form' : message_form,
                'user' : request.user,
        }
        data.update(csrf(request))
        if message_form.is_valid():
            message_form.save()
            return redirect('my_messages')
        else:
            return render_to_response('standard_form.html', data)


def new_message(request):
    if request.method == 'GET':
        data = {
                'form' : MessageForm,
                'user' : request.user,
        }
        data.update(csrf(request))
        return render_to_response('new_message.html', data)
    else:
        data = {
                'form' : MessageForm(request.POST),
                'user' : request.user,
        }
        data.update(csrf(request))
        f = MessageForm(request.POST)
        # Check to see if form is valid
        if f.is_valid():
            message = f.save(commit=False)
            message.teacher = Teacher.objects.get(user=request.user)
            message.save()
            return redirect('my_messages')
        else:
            return render_to_response('new_message.html', data)

def my_messages(request):
    teacher = Teacher.objects.get(user=request.user)
    data = {
            'user' : request.user,
            'messages' : Message.objects.filter(teacher=teacher),
    }
    return render_to_response('my_messages.html', data)

def send_message(student, message, message_type):
    print 'sending message for %s' % (student.first_name)
    event = Event(student=student, message=message,
        date_of_message=datetime.datetime.now(),
        type_of_message=message_type,
        result_of_message=4)
    event.save()

@csrf_exempt
def twilio_call(request, event_id):
    
    event = Event.objects.get(pk=event_id)
    t = template.Template(event.message.text)
    c = template.Context({'student': event.student})
    call_text = t.render(c)
    print request
    # TODO if student not found ?
    # TODO if student.objects.call_notification_ind if false?
    r = twiml.Response()
    r.say(call_text)
    # if request.method == 'GET':

    return HttpResponse(str(r))

def phone_call_completed_handler(request, event_id):
    twilio_call_id = request.POST.CallSid
    call_status = request.POST.CallStatus
    answered_by = request.POST.AnsweredBy

    event = Event(pk=event_id)
    student = event.Student

    if request.POST.Status == 'completed':
        result = 0
    elif request.POST.Status == 'busy':
        result = 1
    elif request.POST.Status == 'no-answer':
        result = 2
    elif request.POST.Status == 'failed':
        result = 3
    else:
        result = -1

    if result != -1:
        event.result_of_message = result
        event.Save()

    return render_to_response("success")

def record_twilio_call(request):
    # load connection
    teacher = Teacher.objects.get(user=request.user)
    # post = request.Post
    conn = TwilioRestClient(
        account = teacher.twilio_account_sid,
        token = teacher.twilio_auth_token)
    conn.calls.create(
        to = '5855763828',
        from_ = teacher.twilio_number,
        url = '%srecording_prompt/' % (BASE_URL))
    return render_to_response("recording_prompt.html")
