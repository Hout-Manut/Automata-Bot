import hikari
import lightbulb

hao_plugin = lightbulb.Plugin("hao")


@hao_plugin.command
@lightbulb.command("hao", "Hao")
@lightbulb.implements(lightbulb.SlashCommand)
async def hao(ctx: lightbulb.SlashContext) -> None:
    await ctx.respond("hao")

def load(bot):
    bot.add_plugin(hao_plugin)
