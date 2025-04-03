import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    RESPONSES_CSV = 'responses.csv'
    FINAL_SURVEY_CSV = 'final_survey.csv'