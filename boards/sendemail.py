import sib_api_v3_sdk
from sib_api_v3_sdk import TransactionalEmailsApi, SendSmtpEmail
from sib_api_v3_sdk.rest import ApiException
from decouple import config
from logging import getLogger
from datetime import datetime
import pytz
from pywebpush import webpush, WebPushException
import json
from allauth.account.models import EmailConfirmationHMAC
from django.conf import settings



logger = getLogger(__name__)

def send_due_date_email_to_user(email, username, task_name, due_date, user_timezone, priority):
    """
    Sends an email using Brevo with task due information and a push notification.
    """
    logger.info(f"Preparing to send email to {email} for task '{task_name}' due on {due_date} with priority {priority}")

    try:
        # Parse the due_date from ISO format
        due_date_obj = datetime.fromisoformat(due_date)

        # Check if due_date is naive or aware
        if due_date_obj.tzinfo is None:
            # If naive, assume it's in UTC and localize it
            utc_timezone = pytz.utc
            due_date_obj = utc_timezone.localize(due_date_obj)

        # Convert due_date to the user's timezone
        user_timezone = pytz.timezone(user_timezone)
        due_date_local = due_date_obj.astimezone(user_timezone)  # Convert to user's timezone

        # Format the date in a user-friendly way
        formatted_due_date = due_date_local.strftime('%B %d, %Y at %I:%M %p')  # Example: "May 13, 2025 at 02:30 PM"
    except Exception as e:
        logger.error(f"Error converting due_date to user's timezone: {e}")
        formatted_due_date = due_date  # Fallback to the original format

    # send formatted priority 
    if priority == 'green':
        updated_priority = 'Low'
    elif priority == 'orange':
        updated_priority = 'Medium'
    elif priority == 'red':
        updated_priority = 'High'
    else:
        updated_priority = 'Without Priority'

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = config('BREVO_API_KEY')

    # Create an instance of the API class
    api_instance = TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    # Define the email content
    send_smtp_email = SendSmtpEmail(
        sender={"email": "dailydoerspace@gmail.com", "name": "DailyDoer"},  # Verified sender email
        to=[{"email": f"{email}"}],
        template_id=2,
        params={
            "username": username,
            "task_name": task_name,
            "priority": updated_priority,
            "due_date": formatted_due_date,  # Use the formatted date
            "email": email,
        },
        headers={"X-Mailin-Tag": "transactional"}
    )

    try:
        # Send the email
        response = api_instance.send_transac_email(send_smtp_email)
        logger.info(f"Email sent to {email} for task '{task_name}' due on {formatted_due_date} with priority {priority}")
        logger.info(f"Brevo Response: {response}")
    except ApiException as e:
        logger.error(f"Error sending email: {e}")

    # Send push notification
    try:
        # Lazy import models to avoid circular import
        from .models import PushSubscription, Notification

        subscriptions = PushSubscription.objects.filter(user__email=email)
        notification_title = "Task Due Reminder"
        notification_body = f"Task '{task_name}' is due on {formatted_due_date} with priority {updated_priority}."

        # Save the notification in the database
        notification = Notification.objects.create(
            user=subscriptions.first().user if subscriptions.exists() else None,
            title=notification_title,
            body=notification_body
        )

        # Inside send_due_date_email_to_user function
        for subscription in subscriptions:
            try:
                webpush(
                    subscription_info=subscription.subscription_info,
                    data=json.dumps({
                        'type': 'TASK_DUE_REMINDER',  # New type for task due notifications
                        'title': notification_title,
                        'body': notification_body,
                        'taskName': task_name,
                        'dueDate': formatted_due_date,
                        'priority': updated_priority,
                        'notification_id': notification.id,  
                        'is_read': notification.is_read,

                    }),
                    vapid_private_key=config('VAPID_PRIVATE_KEY'),
                    vapid_claims={
                        'sub': 'mailto:your-email@example.com'
                    }
                )
                logger.info(f"Push notification sent to {email} for task '{task_name}'")
            except WebPushException as e:
                logger.error(f"Web push failed for {email}: {e}")
    except Exception as e:
        logger.error(f"Error sending push notification: {e}")




# ===========================================  password reset email sending ===========================================


def send_password_reset_email(email, reset_link, username):
    """
    Sends a password reset email using Brevo.
    """
    logger.info(f"Preparing to send password reset email to {email} with reset link: {reset_link}")

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = config('BREVO_API_KEY')

    # Create an instance of the API class
    api_instance = TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    # Define the email content
    send_smtp_email = SendSmtpEmail(
        sender={"email": "dailydoerspace@gmail.com", "name": "DailyDoer"},  # Verified sender email
        to=[{"email": f"{email}"}],
        template_id=3,  # Use a dedicated template ID for password reset emails
        params={
            "reset_link": reset_link,  
            "user_email": email,  
            "username": username,  

        },
        headers={"X-Mailin-Tag": "password_reset"}
    )

    try:
        # Send the email
        response = api_instance.send_transac_email(send_smtp_email)
        logger.info(f"Password reset email sent to {email}. Brevo response: {response}")
    except ApiException as e:
        logger.error(f"Error sending password reset email: {e}")



# ===========================================  send board invitation imaail  ===========================================

# email=email,
# username=request.user.username,
# Board_name={board.name},
# invitation_link=invitation_link,

def send_board_invitation_email(email, username, board_name, invitation_link):
    """
    Sends a board invitation email using Brevo.
    """
    logger.info(f"Preparing to send board invitation email to {email} for board '{board_name}' with link: {invitation_link}")

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = config('BREVO_API_KEY')

    # Create an instance of the API class
    api_instance = TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    # Define the email content
    send_smtp_email = SendSmtpEmail(
        sender={"email": "dailydoerspace@gmail.com", "name": "dailydoer"},  
        to=[{"email": f"{email}"}],
        template_id=5, 
        params={
            "email": email,  
            "username": username,  
            "board_name": board_name,
            "invitation_link": invitation_link, 
        },
        headers={"X-Mailin-Tag": "board_invitation"}
    )
    try:
        logger.info(f"Sending board invitation email to {email} for board '{board_name}'")
        response = api_instance.send_transac_email(send_smtp_email)
        logger.info(f"Board invitation email sent successfully. Brevo response: {response}")
    except Exception as e:
        logger.error(f"Error sending board invitation email: {e}")

# ===========================================  send email confirmation link  ===========================================



def send_email_confirmation(self, email_address):
    """
    Sends an email confirmation using Brevo.
    """
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = config('BREVO_API_KEY')

    api_instance = TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    # Generate the confirmation key
    confirmation = EmailConfirmationHMAC(email_address)
    confirmation_key = confirmation.key

    # Define the email content
    send_smtp_email = SendSmtpEmail(
    sender={"email": "dailydoerspace@gmail.com", "name": "dailydoer"},  
        to=[{"email": email_address.email}],
        template_id=4,  # Replace with your Brevo email confirmation template ID
        params={
            "username": email_address.user.username,
            "confirmation_link": f"{settings.BACKEND_URL}/acc/confirm-email/{confirmation_key}/",  # Use the generated key
        },
        headers={"X-Mailin-Tag": "email_confirmation"}
    )

    try:
        response = api_instance.send_transac_email(send_smtp_email)
        logger.info(f"Email confirmation sent to {email_address.email}. Brevo response: {response}")
    except ApiException as e:
        logger.error(f"Error sending email confirmation: {e}")
        raise Exception("Failed to send email confirmation.")


















# F5F5F5
    