from django.core.management.base import BaseCommand, CommandError
from django import template
from teachercomapp.models import Event, Student, Message
from twilio.rest import TwilioRestClient
from teachercom.settings import *
from django.core.mail import send_mail


class Command(BaseCommand):
    help = "Send messages queued to be sent in the (hopefully recent) past"
    
    def handle(self, *args, **kwargs):
        """ Note: this could be batched to thin out the
            number of requests """
        for event in Event.objects.filter(result_of_message=4):
            conn = TwilioRestClient(
                account = event.teacher.twilio_account_sid,
                token = event.teacher.twilio_auth_token)
            if event.type_of_message == 1:
                # send sms
                msg = event.message
                try:
                    conn.sms.messages.create(
                        to = event.student.phone_number,
                        from_ = event.teacher.twilio_number,
                        body = msg[0:160])
                    event.result_of_message = 0
		    print "Sent SMS to "+ event.student.phone_number
                except:
                    event.result_of_message = 3
                    
            elif event.type_of_message == 2:
                # send voice call
                conn.calls.create(
                    to = event.student.phone_number,
                    from_ = event.teacher.twilio_number,
                    url = '%stwilio_calls/%d/' % (BASE_URL, event.id))
                event.result_of_message=0
        	print "Called "+ event.student.phone_number
                #actually check result later
            elif event.type_of_message == 3:
                # send email message
                message = template.Template(event.message)
                c = template.Context({ 'student' :  event.student })
                send_mail('Message from your teacher', message.render(c), event.teacher.user.email, [event.student.email])
                event.result_of_message = 0
            else:
                pass
                # send email, you know, if we get time
	    event.save()
