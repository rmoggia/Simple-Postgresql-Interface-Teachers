import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'pg-admin-lite-secret-key-change-in-production')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
