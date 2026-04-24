import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN")
SENDER_BOT_TOKEN: str = os.getenv("SENDER_BOT_TOKEN")
OWNER_ID: int = int(os.getenv("OWNER_ID"))
DATABASE_URL: str = os.getenv("DATABASE_URL")
