def analyze_password(password):
    """
    Compute detailed metrics from the password.
    Returns: length, count_upper, count_lower, count_digit, count_special.
    """
    length = len(password)
    count_upper = sum(1 for c in password if c.isupper())
    count_lower = sum(1 for c in password if c.islower())
    count_digit = sum(1 for c in password if c.isdigit())
    special_chars = "!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?`~"
    count_special = sum(1 for c in password if c in special_chars)
    return length, count_upper, count_lower, count_digit, count_special
