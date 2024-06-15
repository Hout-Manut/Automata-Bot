import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
# BOT_ID = int(os.getenv("BOT_ID"))
DEFAULT_GUILDS = os.getenv("GUILDS")
if DEFAULT_GUILDS is not None:
    DEFAULT_GUILDS = [int(x) for x in DEFAULT_GUILDS.split(',')]

DEFAULT_PATH = os.getenv("DEFAULT_PATH")

from .bot import run
from .classes import (
    FA,
    InputStringModal,
    InputFAModal,
    EditFAModal
)
from .screen import MainScreen
from .extensions.error_handler import (
    AutomataError,
    UserError,
    InvalidFAError,
)

__version__ = "0.1"
