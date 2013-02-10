from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

# Create your models here.
class Student(models.Model):
    teachers = models.ManyToManyField('Teacher')
    student_id = models.BigIntegerField()
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    sms_notification_ind = models.BooleanField()
    call_notification_ind = models.BooleanField()
    email_notification_ind = models.BooleanField()
    phone_number = models.CharField(max_length=30)
    email= models.EmailField(max_length=30)

    def __unicode__(self):
        return u'%s %s' % (self.first_name, self.last_name)

class Teacher(models.Model):
    user = models.OneToOneField(User)
    twilio_account_sid = models.CharField(max_length = 128)
    twilio_auth_token = models.CharField(max_length = 128)
    twilio_number = models.CharField(max_length = 20)

    def __unicode__(self):
        return self.user.username

class Message(models.Model):
    teacher = models.ForeignKey('Teacher')
    label = models.CharField(max_length=64)
    text = models.TextField()

class Event(models.Model):
    MESSAGE_TYPES =  (
        (1, 'sms'),
        (2, 'voice'),
        (3, 'email'),
        )
    RESULT_TYPES = (
        (0, 'success'),
        (1, 'busy'),
        (2, 'nopickup'),
        (3, 'failed'),
        (4, 'pending'),
        )
    student = models.ForeignKey('Student')
    message = models.ForeignKey('Message')
    date_of_message = models.DateTimeField()
    type_of_message = models.IntegerField(choices=MESSAGE_TYPES) 
    result_of_message = models.IntegerField(choices = RESULT_TYPES)

class Recording(models.Model):
    event = models.OneToOneField(Event)
    recording_url = models.CharField(max_length=128)