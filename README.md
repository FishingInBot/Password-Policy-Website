# Password Policy Study Website

This project implements a password policy study website that collects password metrics (length, character counts, entropy, etc.) and user feedback for different password policies. The project is built with Flask and is split into multiple modules for maintainability.

## Project Structure

project/
├── app.py                 # Application entry point
├── config.py              # Configuration settings (loads .env)
├── policies.py            # Policy definitions, descriptions, and validation functions
├── routes.py              # Flask route definitions (Blueprint "main")
├── utils.py               # Utility functions (password analysis, entropy, Levenshtein distance)
├── common.txt             # Simple common password list
├── names.txt              # List of names/usernames for Policy 1 checks
├── rockyou.txt            # Extended common password list (or a subset for Policy 4)
├── requirements.txt       # Python dependencies
└── templates/             # HTML templates
    ├── intro.html
    ├── simulation.html
    ├── password_submitted.html
    ├── ratings.html
    ├── final_survey.html
    └── thank_you.html

## Prerequisites

- [Python 3.x](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/)

## Setup Instructions

1. **Clone the Repository**

   Open your terminal (or VS Code terminal) and run:
   
       git clone https://github.com/FishingInBot/Password-Policy-Website.git

   cd into it.

3. **Create a Virtual Environment (Recommended)**

   Create and activate a virtual environment:

   - **On macOS/Linux:**

         python3 -m venv venv
         source venv/bin/activate

   - **On Windows:**

         python -m venv venv
         venv\Scripts\activate

4. **Install Dependencies**

   Install the required Python packages using pip:

         pip install Flask python-dotenv

5. **Create a .env File**

   Create a file named `.env` in the project root and add at least the following:

         SECRET_KEY=your_random_secret_key_here

   Replace `your_random_secret_key_here` with a secure, random string.

6. **Prepare External Files**

   Ensure that `common.txt`, `names.txt`, and `rockyou.txt` are placed in the project root.
   
   - `common.txt`: A small list of common passwords (e.g., "password", "123456", etc.).
   - `names.txt`: A list of names or usernames (one per line) to check against.
   - `rockyou.txt`: An extended password list (or a subset) for Policy 4.

7. **Run the Application**

   Start the Flask app by running:

         python app.py

   The app will run on [http://0.0.0.0:5000](http://0.0.0.0:5000). Open your browser and navigate to that URL to access the website.

## Using VS Code

1. Open the project folder in VS Code.
2. Use the integrated terminal to set up your virtual environment and run the application as described above.
3. VS Code's Python extension will help with linting, debugging, and code navigation.

## Project Overview

- **app.py**: Creates the Flask application and registers the routes.
- **config.py**: Contains configuration settings loaded from environment variables.
- **policies.py**: Contains password policy definitions, descriptions, and validation functions.
- **utils.py**: Contains utility functions for analyzing passwords (entropy, Levenshtein distance, etc.).
- **routes.py**: Contains all the Flask routes grouped under a Blueprint called "main".
- **templates/**: Contains HTML templates for each page in the study.

## Data Collection

- **Password Metrics:**  
  - Length, counts (uppercase, lowercase, digit, special)  
  - Computed entropy, time taken, number of failed attempts  
  - Levenshtein distance computed across the passwords submitted in the session.

- **User Feedback:**  
  - Ratings (scale of 1 to 10) on frustration, perceived strength, and memorability  
  - Open-ended responses for password reuse and reasoning.

- **Advanced Metrics:**  
  - After all policies are completed, the average Levenshtein distance is computed for each policy's password relative to the other policies in the session. These averages, along with a session ID, are stored in a separate CSV file (`levenshtein_results.csv`).

- **Session Linking:**  
  - Each CSV row includes a session ID so that data can be connected across CSV files.

## Additional Notes

- This project is for research purposes. Ensure you review and comply with any relevant privacy or ethical guidelines when collecting user data.
- For production, consider using a proper WSGI server and secure the application further.
