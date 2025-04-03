from flask import Flask, render_template_string, request, redirect, url_for, session
import csv
import time
import os
import random

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

# --- Load External Data for Validation ---
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

# --- Updated Password Policies ---
# We'll use identifiers for policies...
PASSWORD_POLICIES = [
    "Policy 1",
    "Policy 2",
    "Policy 3",
    "Policy 4",
    "Policy 5",
    "Policy 6"
]

# And here is a mapping from policy identifier to a human-readable description.
POLICY_DESCRIPTIONS = {
    "Policy 1": "Minimum 12 characters; at least 3 of 4 character types (uppercase, lowercase, digit, special) required; your name/username must not appear in the password.",
    "Policy 2": "Password must be at least 15 characters long.",
    "Policy 3": "Password must include all four character types (uppercase, lowercase, digit, special).",
    "Policy 4": "Password must not be in our extended common password list.",
    "Policy 5": "Password must be at least 15 characters long OR include all four character types.",
    "Policy 6": "Password length must be between 12 and 30 characters (inclusive)."
}

# --- CSV Files Setup ---
RESPONSES_CSV = 'responses.csv'
if not os.path.exists(RESPONSES_CSV):
    with open(RESPONSES_CSV, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "timestamp", "policy_index", "policy", "password_length",
            "count_upper", "count_lower", "count_digit", "count_special",
            "time_taken", "frustration_rating", "perceived_strength", "memorability",
            "reuse_info", "reasoning"
        ])

FINAL_SURVEY_CSV = 'final_survey.csv'
if not os.path.exists(FINAL_SURVEY_CSV):
    with open(FINAL_SURVEY_CSV, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "timestamp", "year_in", "class_taken", "external_tool_usage", "general_frustrations", "other"
        ])

def analyze_password(password):
    # Compute detailed metrics from the password.
    length = len(password)
    count_upper = sum(1 for c in password if c.isupper())
    count_lower = sum(1 for c in password if c.islower())
    count_digit = sum(1 for c in password if c.isdigit())
    special_chars = "!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?`~"
    count_special = sum(1 for c in password if c in special_chars)
    return length, count_upper, count_lower, count_digit, count_special

def validate_password(password, policy):
    """
    Validate the password against global minimum requirements and policy-specific rules.
    
    Global Minimum Requirements:
      - Length between 8 and 64 characters.
      - At least one uppercase letter and one lowercase letter.
      - Must not be in the simple common password list (common.txt).
    
    Policy-Specific Rules:
      - Policy 1: At least 12 characters; include at least 3 of 4 categories (uppercase, lowercase, digit, special); must not contain any name/username.
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
    
    # Determine character type presence.
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in special_chars for c in password)
    categories = sum([has_upper, has_lower, has_digit, has_special])
    
    # Policy-specific rules:
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
            return False, "For Policy 5, the password must be at least 15 characters long or include all character types (uppercase, lowercase, digit, special)."
        return True, ""
    elif policy == "Policy 6":
        if len(password) < 12 or len(password) > 30:
            return False, "For Policy 6, the password length must be between 12 and 30 characters."
        return True, ""
    else:
        return True, ""

# --- Introductory / Opt-In Page ---
@app.route("/", methods=["GET"])
def intro():
    abstract_text = """
    In today’s digital landscape, strict password policies are crucial for protecting sensitive data, but they often lead to insecure workarounds.
    Our research examines how user behavior and psychological factors like frustration and ease-of-use impact security.
    <br><br>We only store anonymized metrics derived from your password (such as character counts and time taken), never the actual passwords.
    Participation is entirely optional and opt-in, and your privacy is our priority.
    <br><br>Your input will help us develop balanced, user-friendly security policies that truly safeguard digital information.
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <title>Password Policy Study Abstract</title>
      <style>
        body {{
          font-family: Arial, sans-serif;
          margin: 40px;
        }}
        .container {{
          max-width: 700px;
          margin: 0 auto;
          line-height: 1.6;
        }}
        h1 {{
          margin-bottom: 20px;
        }}
        p {{
          margin-bottom: 20px;
        }}
        .abstract {{
          background: #f9f9f9;
          padding: 20px;
          border-radius: 5px;
        }}
        input[type="submit"] {{
          padding: 10px 20px;
          font-size: 16px;
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Password Policy Study</h1>
        <div class="abstract">
          {abstract_text}
        </div>
        <form action="/start" method="POST">
          <input type="submit" value="I Opt-In and Begin">
        </form>
      </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route("/start", methods=["POST"])
def start():
    # Reset session variables for a new participant.
    session["policy_index"] = 0
    # Randomize the order of the policies and store it.
    session["policies_order"] = random.sample(PASSWORD_POLICIES, len(PASSWORD_POLICIES))
    session.pop("current_response", None)
    return redirect(url_for('simulation'))

# --- Simulation: Per-Policy Password Creation and Rating ---
@app.route("/simulation", methods=["GET"])
def simulation():
    policy_index = session.get("policy_index", 0)
    policies = session.get("policies_order", PASSWORD_POLICIES)
    if policy_index >= len(policies):
        return redirect(url_for('final_survey'))
    
    policy = policies[policy_index]
    # Get the human-readable description for this policy.
    policy_description = POLICY_DESCRIPTIONS.get(policy, "")
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Password Creation Study</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 600px; margin: 0 auto; }
        label, p { margin: 10px 0; display: block; }
        input[type="password"], input[type="submit"] {
          width: 100%; padding: 10px; margin-top: 10px; margin-bottom: 20px;
        }
      </style>
      <script>
      {% raw %}
        var startTime = new Date().getTime();
        function setTimeTaken() {
          var endTime = new Date().getTime();
          var timeTaken = (endTime - startTime) / 1000;
          document.getElementById("time_taken").value = timeTaken;
          return true;
        }
      {% endraw %}
      </script>
    </head>
    <body>
      <div class="container">
        <h1>Password Creation Study</h1>
        <p><strong>Policy ({{ current }} of {{ total }}):</strong> {{ policy }} - {{ policy_description }}</p>
        <form action="/password_submitted" method="POST" onsubmit="return setTimeTaken();">
          <input type="hidden" id="time_taken" name="time_taken" value="0">
          <label for="password">Enter your password:</label>
          <input type="password" id="password" name="password" required>
          <input type="submit" value="Submit Password">
        </form>
      </div>
    </body>
    </html>
    """
    return render_template_string(html, policy=policy, policy_description=policy_description, current=policy_index+1, total=len(policies))

@app.route("/password_submitted", methods=["POST"])
def password_submitted():
    policy_index = session.get("policy_index", 0)
    policies = session.get("policies_order", PASSWORD_POLICIES)
    policy = policies[policy_index]
    password = request.form.get("password")
    time_taken = request.form.get("time_taken")
    
    is_valid, error_message = validate_password(password, policy)
    if not is_valid:
        html = """
        <!DOCTYPE html>
        <html>
        <head>
          <title>Password Creation Study</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 600px; margin: 0 auto; }
            label, p { margin: 10px 0; display: block; }
            input[type="password"], input[type="submit"] {
              width: 100%; padding: 10px; margin-top: 10px; margin-bottom: 20px;
            }
            .error { color: red; }
          </style>
          <script>
          {% raw %}
            var startTime = new Date().getTime();
            function setTimeTaken() {
              var endTime = new Date().getTime();
              var timeTaken = (endTime - startTime) / 1000;
              document.getElementById("time_taken").value = timeTaken;
              return true;
            }
          {% endraw %}
          </script>
        </head>
        <body>
          <div class="container">
            <h1>Password Creation Study</h1>
            <p><strong>Policy ({{ current }} of {{ total }}):</strong> {{ policy }}</p>
            <p class="error">{{ error_message }}</p>
            <form action="/password_submitted" method="POST" onsubmit="return setTimeTaken();">
              <input type="hidden" id="time_taken" name="time_taken" value="0">
              <label for="password">Enter your password:</label>
              <input type="password" id="password" name="password" required>
              <input type="submit" value="Submit Password">
            </form>
          </div>
        </body>
        </html>
        """
        return render_template_string(html, policy=policy, current=policy_index+1, total=len(policies), error_message=error_message)
    
    session["current_response"] = {
        "policy_index": policy_index,
        "policy": policy,
        "password": password,
        "time_taken": time_taken
    }
    return redirect(url_for('ratings'))

@app.route("/ratings", methods=["GET"])
def ratings():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Rate Your Experience for this Policy</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 600px; margin: 0 auto; }
        .question { margin: 20px 0; }
        .question label { display: block; margin-bottom: 5px; }
        .scale { font-size: 0.9em; color: #555; margin-bottom: 10px; }
        .options label { display: inline-block; margin-right: 10px; }
        .options input[type="radio"] { margin-right: 3px; }
        textarea { width: 100%; height: 80px; margin-top: 10px; }
        input[type="submit"] { padding: 10px; margin-top: 20px; }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Rate Your Experience for this Policy</h1>
        <form action="/submit" method="POST">
          <div class="question">
            <label>1. On a scale of 1 to 10, how frustrated did you feel while creating the password?</label>
            <div class="scale">(1: Not frustrated, 10: Extremely frustrated)</div>
            <div class="options">
              {% for i in range(1, 11) %}
                <label for="frustration{{ i }}">
                  <input type="radio" id="frustration{{ i }}" name="frustration_rating" value="{{ i }}" required>{{ i }}
                </label>
              {% endfor %}
            </div>
          </div>
          <div class="question">
            <label>2. On a scale of 1 to 10, how strong do you perceive your password to be?</label>
            <div class="scale">(1: Very weak, 10: Very strong)</div>
            <div class="options">
              {% for i in range(1, 11) %}
                <label for="strength{{ i }}">
                  <input type="radio" id="strength{{ i }}" name="perceived_strength" value="{{ i }}" required>{{ i }}
                </label>
              {% endfor %}
            </div>
          </div>
          <div class="question">
            <label>3. On a scale of 1 to 10, how memorable does your password feel?</label>
            <div class="scale">(1: Not at all memorable, 10: Extremely memorable)</div>
            <div class="options">
              {% for i in range(1, 11) %}
                <label for="memorability{{ i }}">
                  <input type="radio" id="memorability{{ i }}" name="memorability" value="{{ i }}" required>{{ i }}
                </label>
              {% endfor %}
            </div>
          </div>
          <div class="question">
            <label>4. Is this password similar to others you have used? Please explain (optional):</label>
            <textarea name="reuse_info" placeholder="E.g., Yes, I use similar passwords on multiple sites, or No, this is unique."></textarea>
          </div>
          <div class="question">
            <label>5. Why did you choose that password? Please explain your reasoning (optional):</label>
            <textarea name="reasoning" placeholder="Your reasoning here..."></textarea>
          </div>
          <input type="submit" value="Submit Ratings">
        </form>
      </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route("/submit", methods=["POST"])
def submit():
    current_response = session.get("current_response")
    if not current_response:
        return redirect(url_for('simulation'))
    
    frustration_rating = request.form.get("frustration_rating")
    perceived_strength = request.form.get("perceived_strength")
    memorability = request.form.get("memorability")
    reuse_info = request.form.get("reuse_info")
    reasoning = request.form.get("reasoning")
    timestamp = int(time.time())
    
    password = current_response["password"]
    policy = current_response["policy"]
    policy_index = current_response["policy_index"]
    time_taken = current_response["time_taken"]
    
    length, count_upper, count_lower, count_digit, count_special = analyze_password(password)
    
    with open(RESPONSES_CSV, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            timestamp, policy_index, policy, length,
            count_upper, count_lower, count_digit, count_special,
            time_taken, frustration_rating, perceived_strength, memorability,
            reuse_info, reasoning
        ])
    
    session["policy_index"] = session.get("policy_index", 0) + 1
    session.pop("current_response", None)
    
    policies = session.get("policies_order", PASSWORD_POLICIES)
    if session["policy_index"] < len(policies):
        return redirect(url_for('simulation'))
    else:
        return redirect(url_for('final_survey'))

@app.route("/final_survey", methods=["GET"])
def final_survey():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Final Survey</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 700px; margin: 0 auto; }
        .question { margin: 20px 0; }
        .question label { display: block; margin-bottom: 10px; }
        select, textarea, input[type="text"] { width: 100%; padding: 10px; margin-top: 5px; margin-bottom: 20px; }
        input[type="submit"] { padding: 10px 20px; margin-top: 20px; }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Final Survey</h1>
        <form action="/final_submit" method="POST">
          <div class="question">
            <label>1. What year are you in?</label>
            <select name="year_in" required>
              <option value="">Select your year</option>
              <option value="Freshman">Freshman</option>
              <option value="Sophomore">Sophomore</option>
              <option value="Junior">Junior</option>
              <option value="Senior">Senior</option>
            </select>
          </div>
          <div class="question">
            <label>2. What class are you taking this in?</label>
            <select name="class_taken" required>
              <option value="">Select your class</option>
              <option value="Computer Science 1">Computer Science 1</option>
              <option value="Computer Science 2">Computer Science 2</option>
              <option value="CS Seminar">CS Seminar</option>
            </select>
          </div>
          <div class="question">
            <label>3. Would you use external tools to remember these passwords? (e.g., password managers, writing them down, etc.)</label>
            <textarea name="external_tool_usage" placeholder="Your answer here..."></textarea>
          </div>
          <div class="question">
            <label>4. Do you have any general frustrations? (Please share any additional thoughts.)</label>
            <textarea name="general_frustrations" placeholder="Your answer here..."></textarea>
          </div>
          <div class="question">
            <label>5. Other (Any additional comments or suggestions):</label>
            <textarea name="other" placeholder="Your answer here..."></textarea>
          </div>
          <input type="submit" value="Submit Final Survey">
        </form>
      </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route("/final_submit", methods=["POST"])
def final_submit():
    year_in = request.form.get("year_in")
    class_taken = request.form.get("class_taken")
    external_tool_usage = request.form.get("external_tool_usage")
    general_frustrations = request.form.get("general_frustrations")
    other = request.form.get("other")
    timestamp = int(time.time())
    
    with open(FINAL_SURVEY_CSV, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            timestamp, year_in, class_taken, external_tool_usage, general_frustrations, other
        ])
    
    return redirect(url_for('thank_you'))

@app.route("/thank_you", methods=["GET"])
def thank_you():
    session.clear()
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Thank You!</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
        .container { max-width: 600px; margin: 0 auto; }
        h1 { margin-bottom: 20px; }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Thank You for Participating!</h1>
        <p>Your responses have been recorded. We appreciate your contribution to improving password policies.</p>
      </div>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
