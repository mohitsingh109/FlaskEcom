import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://auth_user:auth_password@postgres:5432/auth_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = './media'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
