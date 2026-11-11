import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "sentinel_db")
TRANSACTION_LIMIT = int(os.getenv("TRANSACTION_LIMIT", "5000"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1000"))

required = {
    "SUPABASE_URL": SUPABASE_URL,
    "SUPABASE_KEY": SUPABASE_KEY,
    "MONGODB_URI": MONGODB_URI,
}
missing = [name for name, value in required.items() if not value]
if missing:
    raise RuntimeError(
        "Missing environment variables: " + ", ".join(missing) +
        ". Copy .env.example to .env and fill in your credentials."
    )
