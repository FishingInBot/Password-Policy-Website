from flask import Blueprint, render_template, request, redirect, url_for, session
import csv
import time
import random
from policies import PASSWORD_POLICIES, POLICY_DESCRIPTIONS, validate_password
from utils import analyze_password
from config import Config

main = Blueprint('main', __name__)

RESPONSES_CSV = Config.RESPONSES_CSV
FINAL_SURVEY_CSV = Config.FINAL_SURVEY_CSV

@main.route("/", methods=["GET"])
def intro():
    abstract_text = """
    In today’s digital landscape, strict password policies are crucial for protecting sensitive data, but they often lead to insecure workarounds.
    Our research examines how user behavior and psychological factors like frustration and ease-of-use impact security.
    <br><br>We only store anonymized metrics derived from your password (such as character counts and time taken), never the actual passwords.
    Participation is entirely optional and opt-in, and your privacy is our priority.
    <br><br>Your input will help us develop balanced, user-friendly security policies that truly safeguard digital information.
    """
    return render_template("intro.html", abstract_text=abstract_text)

@main.route("/start", methods=["POST"])
def start():
    session["policy_index"] = 0
    session["policies_order"] = random.sample(PASSWORD_POLICIES, len(PASSWORD_POLICIES))
    session.pop("current_response", None)
    return redirect(url_for("main.simulation"))

@main.route("/simulation", methods=["GET"])
def simulation():
    policy_index = session.get("policy_index", 0)
    policies = session.get("policies_order", PASSWORD_POLICIES)
    if policy_index >= len(policies):
        return redirect(url_for("main.final_survey"))
    policy = policies[policy_index]
    policy_description = POLICY_DESCRIPTIONS.get(policy, "")
    return render_template("simulation.html", policy=policy, policy_description=policy_description,
                           current=policy_index+1, total=len(policies))

@main.route("/password_submitted", methods=["POST"])
def password_submitted():
    policy_index = session.get("policy_index", 0)
    policies = session.get("policies_order", PASSWORD_POLICIES)
    policy = policies[policy_index]
    # Get the policy description from the mapping.
    from policies import POLICY_DESCRIPTIONS  # Ensure this import is present.
    policy_description = POLICY_DESCRIPTIONS.get(policy, "")
    
    password = request.form.get("password")
    time_taken = request.form.get("time_taken")
    
    is_valid, error_message = validate_password(password, policy)
    if not is_valid:
        return render_template("password_submitted.html", 
                               policy=policy, 
                               policy_description=policy_description,
                               current=policy_index+1,
                               total=len(policies),
                               error_message=error_message)
    
    session["current_response"] = {
        "policy_index": policy_index,
        "policy": policy,
        "password": password,
        "time_taken": time_taken
    }
    return redirect(url_for("main.ratings"))

@main.route("/ratings", methods=["GET"])
def ratings():
    return render_template("ratings.html")

@main.route("/submit", methods=["POST"])
def submit():
    current_response = session.get("current_response")
    if not current_response:
        return redirect(url_for("main.simulation"))
    
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
        return redirect(url_for("main.simulation"))
    else:
        return redirect(url_for("main.final_survey"))

@main.route("/final_survey", methods=["GET"])
def final_survey():
    return render_template("final_survey.html")

@main.route("/final_submit", methods=["POST"])
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
    
    return redirect(url_for("main.thank_you"))

@main.route("/thank_you", methods=["GET"])
def thank_you():
    session.clear()
    return render_template("thank_you.html")
