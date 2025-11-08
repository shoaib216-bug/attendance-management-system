# =========================================================================
# === THIS IS THE SIMULATED SMS SERVICE ===
# It does NOT connect to any external API. It just prints to the terminal.
# This is 100% reliable for demonstrations and debugging.
# =========================================================================

def send_otp_sms(to_number, otp):
    """
    SIMULATED SMS: This function does not send a real SMS.
    It prints the OTP to the console for development and presentation.
    """
    print("\n" + "="*50)
    print("=== SMS SIMULATOR (OTP) ===")
    print(f"      To: {to_number}")
    print(f"     OTP: {otp}")
    print("="*50 + "\n")
    
    # We always return True so the application thinks the SMS was "sent".
    return True


def send_absent_notification_sms(to_number, student_name, date_str, period):
    """
    SIMULATED SMS: This function does not send a real SMS.
    It prints the absentee notification to the console.
    """
    message = (
        f"Dear Parent, your ward, {student_name}, was marked ABSENT "
        f"for period {period} on {date_str}."
    )
    print("\n" + "="*50)
    print("=== SMS SIMULATOR (Absent Notification) ===")
    print(f"      To: {to_number}")
    print(f" Message: {message}")
    print("="*50 + "\n")
    
    # We always return True so the application thinks the SMS was "sent".
    return True