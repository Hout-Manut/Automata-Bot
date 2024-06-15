import lightbulb
import hikari

main_recent = lightbulb.Plugin('Recent')
@main_recent.command
@lightbulb.option('history', 'Show recent inputs', choices=['a', 'b', 'c'])
@lightbulb.command('recent', 'Show recent inputs')
@lightbulb.implements(lightbulb.SlashCommand)
async def recent(ctx: lightbulb.SlashContext) -> None:
    await ctx.respond('Fuck u panavath')

def load(bot: lightbulb.BotApp):
    bot.add_plugin(main_recent)