import os
from dotenv import load_dotenv

# Load environment variables in the same order as Django settings
load_dotenv('.env.local')
load_dotenv()

print('Database Configuration:')
print(f'DB_ENGINE: {os.environ.get("DB_ENGINE", "django.db.backends.postgresql")}')
print(f'DB_NAME: {os.environ.get("DB_NAME", "trojan_defender")}')
print(f'DB_USER: {os.environ.get("DB_USER", "Not set")}')
print(f'DB_HOST: {os.environ.get("DB_HOST", "localhost")}')
print(f'DB_PORT: {os.environ.get("DB_PORT", "5432")}')