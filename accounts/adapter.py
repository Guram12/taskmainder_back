# filepath: /home/guram/Desktop/task_management_app/task_back/taskmainder/accounts/adapter.py
from allauth.account.adapter import DefaultAccountAdapter
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
import logging

logger = logging.getLogger(__name__)

class CustomAccountAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix, email, context):
        # Log the email content
        logger.debug(f"Sending email to {email} with context: {context}. Template prefix: {template_prefix}")
        
        # Use your custom template for email confirmation
        if template_prefix == 'account/email/email_confirmation':
            template_name = 'accounts/email_confirmation_message.html'
        else:
            template_name = f'{template_prefix}.html'
        
        subject = render_to_string(f'{template_prefix}_subject.txt', context).strip()
        body = render_to_string(template_name, context)
        
        msg = EmailMessage(subject, body, to=[email])
        msg.content_subtype = 'html'  # Set the email content type to HTML
        msg.send()