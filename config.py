import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///plataforma.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,
        'max_overflow': 10,
        'pool_timeout': 30,
        'pool_pre_ping': True,
    }
    UPLOAD_FOLDER = os.path.join('static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    SECRET_KEY = os.environ.get('SECRET_KEY')
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_IMAGE_MIME_TYPES = {
        'image/png',
        'image/jpeg',
        'image/gif',
        'image/webp',
    }


class DevelopmentConfig(Config):
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-me')


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = os.environ.get('SECRET_KEY', 'test-secret-change-me')


class ProductionConfig(Config):
    pass


CONFIG_BY_ENV = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}