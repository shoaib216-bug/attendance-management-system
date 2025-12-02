import re

def is_valid_username(username):
    """
    Checks for a valid admin/staff username based on Instagram-like rules.
    """
    if not (4 <= len(username) <= 30):
        return False, "Username must be between 4 and 30 characters."
    
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_.]*$'
    if not re.match(pattern, username):
        return False, "Username can only contain letters, numbers, underscores (_), and periods (.), and must start with a letter or underscore."
    
    return True, "Username is valid."

def is_valid_password(password):
    """
    Checks for a strong password.
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character."
    return True, "Password is valid."


# =========================================================================
# === NEW VALIDATOR FUNCTIONS ===
# =========================================================================
def is_valid_name(name):
    """
    Checks if a name contains only letters and spaces.
    """
    # This regex pattern allows for alphabet characters (both cases) and spaces.
    # The '+' means one or more occurrences.
    pattern = r'^[a-zA-Z\s]+$'
    if not re.match(pattern, name):
        return False, "Name can only contain letters and spaces."
    return True, "Name is valid."

def is_valid_indian_phone(phone_number):
    """
    Checks if a phone number is a valid 10-digit Indian mobile number.
    """
    # This regex pattern checks for a 10-digit number that starts with 6, 7, 8, or 9.
    pattern = r'^[6-9]\d{9}$'
    if not re.match(pattern, str(phone_number)):
        return False, "Please enter a valid 10-digit Indian mobile number."
    return True, "Phone number is valid."
# =========================================================================