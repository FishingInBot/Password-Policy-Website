import math

def analyze_password(password):
    """
    Compute detailed metrics from the password.
    Returns a tuple: (length, count_upper, count_lower, count_digit, count_special).
    """
    length = len(password)
    count_upper = sum(1 for c in password if c.isupper())
    count_lower = sum(1 for c in password if c.islower())
    count_digit = sum(1 for c in password if c.isdigit())
    special_chars = "!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?`~"
    count_special = sum(1 for c in password if c in special_chars)
    return length, count_upper, count_lower, count_digit, count_special

def compute_entropy(password):
    """Compute the Shannon entropy of the password."""
    if not password:
        return 0
    length = len(password)
    entropy = 0
    for char in set(password):
        p = password.count(char) / length
        entropy += -p * math.log2(p)
    return round(entropy, 2)

def levenshtein(s, t):
    """Compute the Levenshtein distance between strings s and t."""
    if s == t:
        return 0
    if len(s) < len(t):
        return levenshtein(t, s)
    if len(t) == 0:
        return len(s)
    previous_row = list(range(len(t) + 1))
    for i, c1 in enumerate(s):
        current_row = [i + 1]
        for j, c2 in enumerate(t):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]
