import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret_key_pipeline_rca_bot_12345')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'

    # MongoDB settings
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/rca_bot')

    # Ollama settings
    OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434').rstrip('/')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'mistral')

    # GitHub settings
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    if GITHUB_TOKEN == 'your_github_personal_access_token_here':
        GITHUB_TOKEN = None
        
    GITHUB_REPO = os.getenv('GITHUB_REPO')
    if GITHUB_REPO == 'your_github_owner/repo_here':
        GITHUB_REPO = None

    # Folders
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    LOGS_FOLDER = os.path.join(BASE_DIR, 'logs')

    @classmethod
    def init_app(cls, app):
        # Ensure upload and logs folders exist
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(cls.LOGS_FOLDER, exist_ok=True)
