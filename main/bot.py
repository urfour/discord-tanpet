import os
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
DESCRIPTION = '''Bot de la guilde Tan pet de puicenss'''

bot = commands.Bot(command_prefix='!', description=DESCRIPTION)

@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user} (ID : {bot.user.id})')
    print('------')

@bot.command
async def hello(ctx):
    await ctx.send(f'Salut {ctx.author.name} !')

if __name__ == "__main__":
    bot.run(TOKEN)