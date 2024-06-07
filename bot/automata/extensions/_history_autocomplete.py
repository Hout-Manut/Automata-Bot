from typing import Optional

import hikari


class Order(int):
    DATE_ASC = 0
    DATE_DESC = 1


async def history_autocomplete(
    opt: hikari.AutocompleteInteractionOption,
    inter: hikari.AutocompleteInteraction,
    sort_by: Optional[int] = Order.DATE_DESC,
) -> list[str]:
    query: str = opt.value      # The current input in the message field.
    user_id = inter.user.id     # The user ID
    
    history: list[str] = []
    
    # TODO : Get history from db using user_id, sorted.
    
    return history[:25]
