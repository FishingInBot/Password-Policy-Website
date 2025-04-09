from flask import Blueprint, render_template, request, redirect, url_for, session
import csv
import time
import random
import uuid
from policies import PASSWORD_POLICIES, POLICY_DESCRIPTIONS, validate_password
from utils import analyze_password, compute_entropy, levenshtein
from config import Config
import os

main = Blueprint('main', __name__)

RESPONSES_CSV = Config.RESPONSES_CSV
FINAL_SURVEY_CSV = Config.FINAL_SURVEY_CSV
LEVENSHTEIN_CSV = "levenshtein_results.csv"

# Ensure the responses CSV has the proper header (include session_id and new metrics)
if not os.path.exists(RESPONSES_CSV):
    with open(RESPONSES_CSV, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "timestamp", "session_id", "policy_index", "policy", "password_length",
            "count_upper", "count_lower", "count_digit", "count_special",
            "time_taken", "entropy", "failed_attempts",
            "frustration_rating", "perceived_strength", "memorability",
            "reuse_info", "reasoning"
        ])

# Ensure the final survey CSV has the proper header (include session_id and new metrics)
if not os.path.exists(FINAL_SURVEY_CSV):
    with open(FINAL_SURVEY_CSV, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "timestamp", "session_id", "year_in", "class_taken",
            "external_tool_usage", "general_frustrations", "other"
        ])

# Ensure the levenshtein results CSV has a header
if not os.path.exists(LEVENSHTEIN_CSV):
    with open(LEVENSHTEIN_CSV, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        header = ["session_id"] + [f"avg_distance_policy_{i+1}" for i in range(len(PASSWORD_POLICIES))] + ["avg_of_avgs"]
        writer.writerow(header)

@main.route("/", methods=["GET"])
def intro():
    abstract_text = """
    In today’s digital landscape, strict password policies are crucial for protecting sensitive data, but they often lead to insecure workarounds.
    Our research examines how user behavior and psychological factors like frustration and ease-of-use impact security.
    <br><br>We only store anonymized metrics derived from your password (such as character counts, time taken, and computed entropy), never the actual password.
    Participation is entirely optional and opt-in, and your privacy is our priority. The policies will be served in a randomized order, and you will be asked to create a password for each policy.
    <br><br>Your input will help us develop balanced, user-friendly security policies that truly safeguard digital information.
    """
    return render_template("intro.html", abstract_text=abstract_text)

@main.route("/start", methods=["POST"])
def start():
    # Generate a unique session ID and initialize a list to store each password response.
    session["session_id"] = str(uuid.uuid4())
    session["policy_index"] = 0
    session["policies_order"] = random.sample(PASSWORD_POLICIES, len(PASSWORD_POLICIES))
    session["password_responses"] = []  # Will store dictionaries for each policy response.
    session.pop("current_response", None)
    # Also initialize failed attempts counter.
    session["failed_attempts"] = 0
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
    policy_description = POLICY_DESCRIPTIONS.get(policy, "")
    
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")
    time_taken = request.form.get("time_taken")
    
    # Check that password and confirmation match.
    if password != confirm_password:
        session["failed_attempts"] = session.get("failed_attempts", 0) + 1
        error_message = "Passwords do not match. Please re-enter them."
        return render_template("password_submitted.html",
                               policy=policy,
                               policy_description=policy_description,
                               current=policy_index+1,
                               total=len(policies),
                               error_message=error_message)
    
    # Validate the password.
    is_valid, error_message = validate_password(password, policy)
    if not is_valid:
        session["failed_attempts"] = session.get("failed_attempts", 0) + 1
        return render_template("password_submitted.html",
                               policy=policy,
                               policy_description=policy_description,
                               current=policy_index+1,
                               total=len(policies),
                               error_message=error_message)
    
    # Compute entropy.
    entropy = compute_entropy(password)
    # (Levenshtein distance will be computed later across responses.)
    failed_attempts = session.get("failed_attempts", 0)
    # Reset failed attempts counter for the next policy.
    session["failed_attempts"] = 0
    
    # Save the current response in session.
    current_response = {
        "policy_index": policy_index,
        "policy": policy,
        "password": password,
        "time_taken": time_taken,
        "entropy": entropy,
        "failed_attempts": failed_attempts
    }
    session["current_response"] = current_response
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
    entropy = current_response["entropy"]
    failed_attempts = current_response["failed_attempts"]
    
    length, count_upper, count_lower, count_digit, count_special = analyze_password(password)
    session_id = session.get("session_id")
    
    # Write the response row to the RESPONSES_CSV.
    with open(RESPONSES_CSV, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            timestamp, session_id, policy_index, policy, length,
            count_upper, count_lower, count_digit, count_special,
            time_taken, entropy, failed_attempts,
            frustration_rating, perceived_strength, memorability,
            reuse_info, reasoning
        ])
    
    # Append the raw password response to the session list (for later Levenshtein computation).
    password_responses = session.get("password_responses", [])
    password_responses.append({
        "policy_index": policy_index,
        "policy": policy,
        "password": password
    })
    session["password_responses"] = password_responses
    
    # Move to the next policy.
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
    session_id = session.get("session_id")
    
    with open(FINAL_SURVEY_CSV, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            timestamp, session_id, year_in, class_taken, external_tool_usage, general_frustrations, other
        ])
    
    # Now, compute average Levenshtein distances across all passwords in this session.
    password_responses = session.get("password_responses", [])
    # Sort responses by policy_index (to keep consistent order)
    password_responses = sorted(password_responses, key=lambda r: r["policy_index"])
    avg_distances = []
    num_responses = len(password_responses)
    # For each response, compute average distance to all others.
    for i, resp_i in enumerate(password_responses):
        distances = []
        for j, resp_j in enumerate(password_responses):
            if i != j:
                d = levenshtein(resp_i["password"], resp_j["password"])
                distances.append(d)
        avg = sum(distances) / len(distances) if distances else 0
        avg_distances.append(round(avg, 2))
    # Lets get the average of the averages and append it to the list.
    avg_of_avgs = round(sum(avg_distances) / len(avg_distances), 2)
    avg_distances.append(avg_of_avgs)
    
    # Write the results to LEVENSHTEIN_CSV with the session id.
    with open(LEVENSHTEIN_CSV, "a", newline='') as csvfile:
        writer = csv.writer(csvfile)
        row = [session_id] + avg_distances
        writer.writerow(row)
    
    return redirect(url_for("main.thank_you"))

@main.route("/thank_you", methods=["GET"])
def thank_you():
    session.clear()
    return render_template("thank_you.html")
