from __future__ import annotations

import re
from datetime import timedelta
from typing import Coroutine

import hikari
import hikari.errors
import lightbulb
import miru

from . import buttons
from .classes import FA, Color, FAStringResult
from .extensions import error_handler as error




class FAController:

    def __init__(
        self,
        inter: lightbulb.SlashContext
    ) -> None:

        inter.interaction.command_name
        pass


    async def respond(self) -> None:
        ...
