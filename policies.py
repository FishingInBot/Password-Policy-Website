import os

# Load simple common passwords from common.txt (one per line)
COMMON_PASSWORDS = set()
if os.path.exists("common.txt"):
    with open("common.txt", "r", encoding="utf-8") as f:
        for line in f:
            COMMON_PASSWORDS.add(line.strip().lower())

# Load names/usernames from names.txt (one per line)
NAMES = set()
if os.path.exists("names.txt"):
    with open("names.txt", "r", encoding="utf-8") as f:
        for line in f:
            NAMES.add(line.strip().lower())

# Load extended common password list from rockyou.txt (or a subset) for Policy 4
ROCKYOU_PASSWORDS = set()
if os.path.exists("rockyou.txt"):
    with open("rockyou.txt", "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            ROCKYOU_PASSWORDS.add(line.strip().lower())

# Define our policies.
PASSWORD_POLICIES = [
    "Policy 1",
    "Policy 2",
    "Policy 3",
    "Policy 4",
    "Policy 5",
    "Policy 6"
]

# Human-readable descriptions.
POLICY_DESCRIPTIONS = {
    "Policy 1": "Minimum 12 characters; at least 3 of 4 character types (uppercase, lowercase, digit, special) required; your name/ranger ID must not appear in the password.",
    "Policy 2": "Password must be at least 15 characters long and include a capital and lowercase letter.",
    "Policy 3": "Password must include all four character types (uppercase, lowercase, digit, special). It must still be at least 8 characters long.",
    "Policy 4": "Password must not be in our extended common password list. It must still be 8 characters long and include a capital and lowercase letter.",
    "Policy 5": "Password must be at least 15 characters long with a capital and lowercase letter OR include all four character types and be at least 8 characters long.",
    "Policy 6": "Password length must be between 12 and 30 characters (inclusive) and include a capital and lowercase letter."
}

def validate_password(password, policy):
    """
    Validate a password against global minimum requirements and policy-specific rules.
    
    Global Minimum Requirements:
      - Length between 8 and 64 characters.
      - At least one uppercase letter and one lowercase letter.
      - Must not be in the simple common password list.
    
    Policy-Specific Rules:
      - Policy 1: At least 12 characters; at least 3 of 4 categories; must not contain any name/username.
      - Policy 2: At least 15 characters.
      - Policy 3: Must include all four character types.
      - Policy 4: Must not appear in the extended list (rockyou.txt).
      - Policy 5: Either at least 15 characters OR include all four character types.
      - Policy 6: Length must be between 12 and 30 characters.
    """
    special_chars = "!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?`~"
    
    # Global minimum requirements:
    if len(password) < 8 or len(password) > 64:
        return False, "Password must be between 8 and 64 characters long."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    if password.lower() in COMMON_PASSWORDS:
        return False, "Password is too common."
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in special_chars for c in password)
    categories = sum([has_upper, has_lower, has_digit, has_special])
    
    if policy == "Policy 1":
        if len(password) < 12:
            return False, "For Policy 1, the password must be at least 12 characters long."
        if categories < 3:
            return False, "For Policy 1, the password must include at least 3 of the following: uppercase, lowercase, digit, and special character."
        lower_password = password.lower()
        for name in NAMES:
            if name and name in lower_password:
                return False, "For Policy 1, your name/username must not appear in the password."
        return True, ""
    elif policy == "Policy 2":
        if len(password) < 15:
            return False, "For Policy 2, the password must be at least 15 characters long."
        return True, ""
    elif policy == "Policy 3":
        if not (has_upper and has_lower and has_digit and has_special):
            return False, "For Policy 3, the password must contain an uppercase letter, a lowercase letter, a digit, and a special character."
        return True, ""
    elif policy == "Policy 4":
        if password.lower() in ROCKYOU_PASSWORDS:
            return False, "For Policy 4, the password is too common according to our extended list."
        return True, ""
    elif policy == "Policy 5":
        if len(password) < 15 and not (has_upper and has_lower and has_digit and has_special):
            return False, "For Policy 5, the password must be at least 15 characters long or include all character types."
        return True, ""
    elif policy == "Policy 6":
        if len(password) < 12 or len(password) > 30:
            return False, "For Policy 6, the password length must be between 12 and 30 characters."
        return True, ""
    else:
        return True, ""
