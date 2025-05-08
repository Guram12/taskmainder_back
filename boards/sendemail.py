import sib_api_v3_sdk  # Import the main module
from sib_api_v3_sdk import TransactionalEmailsApi, SendSmtpEmail
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint
from decouple import config


def send_test_email_with_brevo():
    # Configure API key authorization
    configuration = sib_api_v3_sdk.Configuration()
    
    configuration.api_key['api-key'] = config('BREVO_API_KEY')  
    
    # Create an instance of the API class
    api_instance = TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    # Define the email details
    send_smtp_email = SendSmtpEmail(
        to=[{"email": "guram.shanidze.33@gmail.com", "name": "Guram"}],  # Replace with recipient details
        template_id=2, 
        params={
            "name": "Guram",  
            "task_name": "Example Task",
            "due_date": "2025-05-10"
        }
    )

    try:
        # Send the email
        api_response = api_instance.send_transac_email(send_smtp_email)
        pprint(api_response)
        print("Email sent successfully using Brevo!")
    except ApiException as e:
        print(f"Exception when calling TransactionalEmailsApi->send_transac_email: {e}")


# from boards.sendemail import send_test_email_with_brevo
# send_test_email_with_brevo()