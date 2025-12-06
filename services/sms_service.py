from flask import current_app
from twilio.rest import Client

def _send_twilio_sms(to_number, message_body):
    """A unified internal function to send any SMS message using the Twilio API."""
    try:
        account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
        auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
        twilio_number = current_app.config.get('TWILIO_PHONE_NUMBER')
        
        if not all([account_sid, auth_token, twilio_number]):
            print("!!! TWILIO ERROR: Credentials are not configured in .env file. !!!")
            return False

        if not to_number.startswith('+'):
            to_number = f'+91{to_number}'

        client = Client(account_sid, auth_token)
        
        message = client.messages.create(
            body=message_body,
            from_=twilio_number,
            to=to_number
        )
        
        print(f"--- Twilio SMS initiated to {to_number}: SID {message.sid} ---")
        return True
        
    except Exception as e:
        print(f"!!! TWILIO SMS FAILED. Error: {e} !!!")
        return False

def send_otp_sms(to_number, otp):
    """Formats and sends an OTP message via Twilio."""
    print(f"--- Attempting to send OTP to {to_number} via Twilio ---")
    message = f"Your OTP for Attendance Management is: {otp}. It is valid for 10 minutes."
    return _send_twilio_sms(to_number, message)

def send_absent_notification_sms(to_number, student_name, date_str, period, subject, time_str):
    """Formats and sends a custom absentee notification via Twilio."""
    print(f"--- Attempting to send ABSENT notification to {to_number} via Twilio ---")
    
    # The time_str passed here is now in IST format (e.g., "10:30 AM")
    message = (
        f"Attendance Alert: Your ward, {student_name}, was marked ABSENT "
        f"for period {period} ({subject}) on {date_str} at approx {time_str}. "
        f"- Attendance Mgmt"
    )
    return _send_twilio_sms(to_number, message)