import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "Sambit@123"),
    "database": os.getenv("DB_NAME", "quiz_app_db"),
}

QUESTIONS_PER_QUIZ = int(os.getenv("QUESTIONS_PER_QUIZ", 5))
TIME_PER_QUESTION = int(os.getenv("TIME_PER_QUESTION", 15))
