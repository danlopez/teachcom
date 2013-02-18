# Create your views here.
from django.core.context_processors import csrf
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from teachercomapp.models import Student, Message, Event, Teacher
from teachercomapp.forms import MessageForm, StudentForm, EventForm
import datetime
import csv
import StringIO
from twilio import twiml
from django import template
from django.db.models import Q
from twilio.rest import TwilioRestClient
from teachercom.settings import *
from pprint import pprint

@cache_page(1)
def index(request):
    if request.user.is_authenticated():
        teacher = Teacher.objects.get(user = request.user)
        calls_made = Event.objects.filter(teacher=teacher).filter(type_of_message=2).count()
        sms_made = Event.objects.filter(teacher=teacher).filter(type_of_message=1).count()
        emails_sent = Event.objects.filter(teacher=teacher).filter(type_of_message=3).count()
        data = {
            'user': request.user,
            'teacher' : teacher,
            'events' : Event.objects.filter(teacher=teacher).order_by('-date_of_message')[:5],
            'num_calls_possible' : teacher.credits / 2,
            'num_calls_made' : calls_made,
            'num_sms_made' : sms_made,
            'num_emails_sent' : emails_sent,
            'minutes_saved' : (calls_made * 5) + sms_made + emails_sent
        }
        return render_to_response('dashboard.html', data)
    else:
        return render_to_response('index.html')

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
                send_message(student, message, 1, request)
            if student.call_notification_ind:
                send_message(student, message, 2, request)
            if student.email_notification_ind:
                send_message(student, message, 3, request)
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
            'events': Event.objects.filter(teacher = teacher),
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

def new_event(request):
    if request.method == 'GET':
        data = {
                'form' : EventForm,
                'user' : request.user,
        }
        data.update(csrf(request))
        return render_to_response('new_event.html', data)
    else:
        data = {
                'form' : EventForm(request.POST),
                'user' : request.user,
        }
        data.update(csrf(request))
        f = EventForm(request.POST)
        # Check to see if form is valid
        if f.is_valid():
            event = f.save(commit=False)
            event.teacher = Teacher.objects.get(user=request.user)
            event.save()
            return redirect('call_log')
        else:
            return render_to_response('new_event.html', data)


def my_messages(request):
    teacher = Teacher.objects.get(user=request.user)
    data = {
            'user' : request.user,
            'messages' : Message.objects.filter(teacher=teacher),
    }
    return render_to_response('my_messages.html', data)

def send_message(student, message, message_type, request):
    teacher = Teacher.objects.get(user=request.user)
    print 'sending message for %s' % (student.first_name)
    new_message = template.Template(message.text)
    c = template.Context({ 'student' : student })
    print new_message.render(c)
    event = Event(student=student, 
        message=new_message.render(c), 
        teacher=teacher,
        date_of_message=datetime.datetime.now(),
        type_of_message=message_type,
        result_of_message=4)
    print "Message" + event.message
    event.save()

@csrf_exempt
def twilio_call(request, event_id):
    event = Event.objects.get(pk=event_id)
    call_text = event.message
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
    if request.method == 'GET':
        teacher = Teacher.objects.get(user=request.user)
        # post = request.Post
        conn = TwilioRestClient(
            account = teacher.twilio_account_sid,
            token = teacher.twilio_auth_token)
        call = conn.calls.create(
            to = '5855763828',
            from_ = teacher.twilio_number,
            url = '%srecord_twiml/' % (BASE_URL))
    print call.sid
    #should redirect to a message object.  Should create a new data type 'recordings'
        #can be attached to a message
    return render_to_response("recording_prompt.html")

def get_records(request):
    event_id = 11
    event = Event.objects.get(id = event_id)
    plaintext = template.Template(event.message.text)
    context = template.Context({'student': event.student})
    print plaintext.render(context)
    
    return render_to_response("recording_prompt.html")
@csrf_exempt
def confirm_recording(request):
    data = ({
        'user': request.user,
        })

    if request.method =='POST': #coming from confirm_recording
        if (request.POST.Digits!=2):
            r = twiml.Response()
            r.say("Thanks! Goodbye.")
            return HttpResponse(str(r))
        else:
            print request
            #erase previous recording, should be in request
            data = ({
                'user': request.user,
                'recordings': recordings,
                })
            return render_to_response("recording_prompt.html")
    else : #coming from recording_prompt (request.GET)
        return render_to_response("confirm_recording.html", data)
        #render some more twiml
        #return redirect('my_messages')

@csrf_exempt
def record_twiml(request):
    print request
    return render_to_response("recording_prompt.html")