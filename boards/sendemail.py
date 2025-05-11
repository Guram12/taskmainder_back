import sib_api_v3_sdk  # Import the main module
from sib_api_v3_sdk import TransactionalEmailsApi, SendSmtpEmail
from sib_api_v3_sdk.rest import ApiException
from decouple import config
from logging import getLogger


logger = getLogger(__name__)

def send_due_date_email_to_user(email, task_name, due_date):
    """
    Sends an email using Brevo with task due information.
    """
    logger.info(f"Preparing to send email to ------------------------ {email} for task '{task_name}' due on {due_date}---------------------------")


    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = config('BREVO_API_KEY')

    # Create an instance of the API class
    api_instance = TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    # Define the email content
    send_smtp_email = SendSmtpEmail(
        sender={"email": "guramshanidze44@gmail.com", "name": "Task Reminder"},  # Verified sender email
        to=[{"email": f"{email}"}],
        template_id=2,
        params={
            "task_name": task_name,
            "due_date": due_date,
            'email': email,

        },
        headers={"X-Mailin-Tag": "transactional"}
    )

    try:
        # Send the email
        response = api_instance.send_transac_email(send_smtp_email)
        logger.info(f"Email sent to ===================>>>>  {email} for task '{task_name}' due on {due_date}")
        logger.info(f"Brevo Response  ===================>>>> : {response}")
    except ApiException as e:
        logger.error(f"Error sending email: {e}")


# from boards.sendemail import send_test_email_with_brevo
# send_test_email_with_brevo('guramshanidze44@gmail.com', 'Test -3- Task', '2025-05-09T12:30:00+00:00')


# -----------------------------
# guram.shanidze.33@gmail.com
# guramshanidze44@gmail.com
# ninomarishanidze@gmail.com



# ===========================================  password reset emaail sending ===========================================


def send_password_reset_email(email, reset_link):
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
        sender={"email": "guramshanidze44@gmail.com", "name": "Task Reminder"},  # Verified sender email
        to=[{"email": f"{email}"}],
        template_id=3,  # Use a dedicated template ID for password reset emails
        params={
            "reset_link": reset_link,  # Pass the reset link to the template
            "user_email": email,  # Include the user's email in the template
        },
        headers={"X-Mailin-Tag": "password_reset"}
    )

    try:
        # Send the email
        response = api_instance.send_transac_email(send_smtp_email)
        logger.info(f"Password reset email sent to {email}. Brevo response: {response}")
    except ApiException as e:
        logger.error(f"Error sending password reset email: {e}")