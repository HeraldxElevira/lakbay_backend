import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://neondb_owner:npg_fpQHPM1e2AsV@ep-red-truth-aq42gdn6-pooler.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require"
)

def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn