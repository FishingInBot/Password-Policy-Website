from flask import Flask, render_template_string, request, redirect, url_for, session
import csv
import time
import os

app = Flask(__name__)
app.secret_key = "replace_with_a_secure_random_key"  # For session management

# Define sample password policies.
PASSWORD_POLICIES = [
    "Password must be at least 8 characters long.",
    "Password must be at least 12 characters long and contain at least one special character.",
    "Password must include at least one uppercase letter, one lowercase letter, and one digit.",
    "Password must be a passphrase of three or more words.",
]

CSV_FILE = 'responses.csv'

# Create CSV file with header if it doesn't exist.
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "timestamp", "policy_index", "policy", "password_length",
            "count_upper", "count_lower", "count_digit", "count_special",
            "time_taken", "frustration_rating", "perceived_strength", "memorability"
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

@app.route("/", methods=["GET"])
def index():
    # Initialize the session index if it's not already set.
    if "policy_index" not in session:
        session["policy_index"] = 0

    index_value = session["policy_index"]

    # If all policies have been completed, go to the thank-you page.
    if index_value >= len(PASSWORD_POLICIES):
        return redirect(url_for('thank_you'))

    policy = PASSWORD_POLICIES[index_value]
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Password Creation Study</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 600px; margin: 0 auto; }
        label, p { margin-top: 10px; margin-bottom: 10px; display: block; }
        input[type="password"], input[type="submit"] {
          width: 100%; padding: 10px; margin-top: 10px; margin-bottom: 20px;
        }
      </style>
      <script>
        // Record the start time when the page loads.
        var startTime = new Date().getTime();
        function setTimeTaken() {
          var endTime = new Date().getTime();
          var timeTaken = (endTime - startTime) / 1000; // time in seconds
          document.getElementById("time_taken").value = timeTaken;
          return true;
        }
      </script>
    </head>
    <body>
      <div class="container">
        <h1>Password Creation Study</h1>
        <p><strong>Policy ({{ index }} of {{ total }}):</strong> {{ policy }}</p>
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
    return render_template_string(html, policy=policy, index=index_value+1, total=len(PASSWORD_POLICIES))

@app.route("/password_submitted", methods=["POST"])
def password_submitted():
    # Retrieve password creation data.
    policy_index = session.get("policy_index", 0)
    policy = PASSWORD_POLICIES[policy_index]
    password = request.form.get("password")
    time_taken = request.form.get("time_taken")
    # Temporarily store the password data in the session.
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
      <title>Rate Your Experience</title>
      <style>
        body { 
          font-family: Arial, sans-serif; 
          margin: 40px; 
        }
        .container { 
          max-width: 600px; 
          margin: 0 auto; 
        }
        .question { 
          margin: 20px 0; 
        }
        .question label { 
          display: block; 
          margin-bottom: 10px; 
        }
        .options label { 
          display: inline-block; 
          margin-right: 20px; 
        }
        .options input[type="radio"] { 
          margin-right: 5px; 
        }
        input[type="submit"] { 
          padding: 10px; 
          margin-top: 20px; 
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Rate Your Experience</h1>
        <form action="/submit" method="POST">
          <div class="question">
            <label>How frustrated did you feel? (1 = Not at all, 5 = Very frustrated)</label>
            <div class="options">
              <label for="frustration1">
                <input type="radio" id="frustration1" name="frustration_rating" value="1" required>1
              </label>
              <label for="frustration2">
                <input type="radio" id="frustration2" name="frustration_rating" value="2">2
              </label>
              <label for="frustration3">
                <input type="radio" id="frustration3" name="frustration_rating" value="3">3
              </label>
              <label for="frustration4">
                <input type="radio" id="frustration4" name="frustration_rating" value="4">4
              </label>
              <label for="frustration5">
                <input type="radio" id="frustration5" name="frustration_rating" value="5">5
              </label>
            </div>
          </div>
          <div class="question">
            <label>How strong do you think your password is? (1 = Weak, 5 = Very strong)</label>
            <div class="options">
              <label for="strength1">
                <input type="radio" id="strength1" name="perceived_strength" value="1" required>1
              </label>
              <label for="strength2">
                <input type="radio" id="strength2" name="perceived_strength" value="2">2
              </label>
              <label for="strength3">
                <input type="radio" id="strength3" name="perceived_strength" value="3">3
              </label>
              <label for="strength4">
                <input type="radio" id="strength4" name="perceived_strength" value="4">4
              </label>
              <label for="strength5">
                <input type="radio" id="strength5" name="perceived_strength" value="5">5
              </label>
            </div>
          </div>
          <div class="question">
            <label>How memorable do you think your password is? (1 = Not at all, 5 = Very memorable)</label>
            <div class="options">
              <label for="memorability1">
                <input type="radio" id="memorability1" name="memorability" value="1" required>1
              </label>
              <label for="memorability2">
                <input type="radio" id="memorability2" name="memorability" value="2">2
              </label>
              <label for="memorability3">
                <input type="radio" id="memorability3" name="memorability" value="3">3
              </label>
              <label for="memorability4">
                <input type="radio" id="memorability4" name="memorability" value="4">4
              </label>
              <label for="memorability5">
                <input type="radio" id="memorability5" name="memorability" value="5">5
              </label>
            </div>
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
    # Retrieve the stored password creation data.
    current_response = session.get("current_response")
    if not current_response:
        return redirect(url_for('index'))
    
    # Get ratings from the form.
    frustration_rating = request.form.get("frustration_rating")
    perceived_strength = request.form.get("perceived_strength")
    memorability = request.form.get("memorability")
    timestamp = int(time.time())
    
    password = current_response["password"]
    policy = current_response["policy"]
    policy_index = current_response["policy_index"]
    time_taken = current_response["time_taken"]
    
    # Analyze the password for various character counts.
    length, count_upper, count_lower, count_digit, count_special = analyze_password(password)
    
    # Append the result to the CSV file.
    with open(CSV_FILE, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            timestamp, policy_index, policy, length,
            count_upper, count_lower, count_digit, count_special,
            time_taken, frustration_rating, perceived_strength, memorability
        ])
    
    # Increment the policy index for the next policy and clear the current response.
    session["policy_index"] = session.get("policy_index", 0) + 1
    session.pop("current_response", None)
    
    if session["policy_index"] < len(PASSWORD_POLICIES):
        return redirect(url_for('index'))
    else:
        return redirect(url_for('thank_you'))

@app.route("/thank_you", methods=["GET"])
def thank_you():
    # Optionally, clear session data for a new participant.
    session.pop("policy_index", None)
    return "<h2>Thank you for participating in our study!</h2>"

if __name__ == "__main__":
    app.run(debug=True)
