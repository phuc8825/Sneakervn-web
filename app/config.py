import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'super-secret-key-change-in-production')

    # Supabase PostgreSQL — dùng connection pooling (port 6543) cho production
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres.mstgukpgzlkcqzzanvia:phanthienphuc88@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Cần thiết khi dùng Supabase pooler (PgBouncer) — tắt pre-ping để tránh lỗi
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # Flask-Mail (Gmail SMTP)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('EMAIL_USER')
    MAIL_PASSWORD = os.getenv('EMAIL_PASS')
    MAIL_DEFAULT_SENDER = os.getenv('EMAIL_USER')

    # Upload ảnh sản phẩm — đặt file vào app/static/uploads/<tên_file>
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB