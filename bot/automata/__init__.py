import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
# BOT_ID = int(os.getenv("BOT_ID"))
DEFAULT_GUILDS = os.getenv("GUILDS")
if DEFAULT_GUILDS is not None:
    DEFAULT_GUILDS = [int(x) for x in DEFAULT_GUILDS.split(',')]

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

if DB_HOST is None or DB_USER is None or DB_PASSWORD is None or DB_NAME is None:
    raise ValueError("Database environment variables are not set.")

if TOKEN is None:
    raise ValueError("Bot token is not set.")

DB_PORT = os.getenv("DB_PORT") or "3306"

from .bot import run
from .classes import (
    FA,
    InputStringModal,
    InputFAModal,
    EditFAModal,
)
from .screen import AutomataMenu, MainScreen, TestStringScreen
from .extensions.error_handler import (
    AutomataError,
    UserError,
    InvalidFAError,
)

__version__ = "0.1"
