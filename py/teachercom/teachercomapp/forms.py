from django import forms
from registration.forms import RegistrationForm
from django.forms import Form

import models
from models import Message
from registration.models import RegistrationProfile

attrs_dict = { 'class': 'required' }

class UserRegistrationForm(RegistrationForm):
    twilio_account_sid = forms.CharField(widget=forms.TextInput(attrs=attrs_dict))
    twilio_auth_token = forms.CharField(widget=forms.TextInput(attrs=attrs_dict))
    twilio_number = forms.CharField(widget=forms.TextInput(attrs=attrs_dict))

class MessageForm(Form):
    # class Meta:
    #     model=Message
    label = forms.CharField(widget=forms.TextInput(attrs=attrs_dict))
     # teacher = forms.ChoiceField()
    text = forms.CharField(widget=forms.Textarea(attrs=attrs_dict))
    # new_field = forms.CharField(widget=forms.TextInput(attrs=attrs_dict))