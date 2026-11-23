
import os
from dotenv import load_dotenv

# Load environment variables from the project root .env file
load_dotenv()

# Stripe configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

if not STRIPE_SECRET_KEY:
    raise ValueError("STRIPE_SECRET_KEY is not configured")

# Stripe webhook configuration
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

if not STRIPE_WEBHOOK_SECRET:
    raise ValueError("STRIPE_WEBHOOK_SECRET is not configured")

# PostgreSQL configuration
DATABASE_URL = os.getenv("DATABASE_URL")
