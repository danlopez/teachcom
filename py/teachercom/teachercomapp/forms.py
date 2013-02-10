from django import forms
from registration.forms import RegistrationForm
from django.forms import Form, ModelForm

import models
from models import Message, Student, Event
from registration.models import RegistrationProfile

attrs_dict = { 'class': 'required' }

class UserRegistrationForm(RegistrationForm):
    twilio_account_sid = forms.CharField(widget=forms.TextInput(attrs=attrs_dict))
    twilio_auth_token = forms.CharField(widget=forms.TextInput(attrs=attrs_dict))
    twilio_number = forms.CharField(widget=forms.TextInput(attrs=attrs_dict))

class MessageForm(ModelForm):
    class Meta:
        model = Message
        exclude = ('teacher')
    #label = forms.CharField(widget=forms.TextInput(attrs=attrs_dict))
    # teacher = forms.ChoiceField()
    #text = forms.CharField(widget=forms.Textarea(attrs=attrs_dict))
    # new_field = forms.CharField(widget=forms.TextInput(attrs=attrs_dict))

class StudentForm(ModelForm):
    class Meta:
        model = Student
        exclude = ('teachers',)

class EventForm(ModelForm):
    class Meta:
        model = Event
        exclude = ('teacher','date_of_message')
