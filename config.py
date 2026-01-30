# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from same directory as config.py (backend/)
basedir = Path(__file__).parent.absolute()
env_path = basedir / '.env'

load_dotenv(env_path)

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret")
    AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
    AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
    DATABASE_PATH = "database.db"

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}