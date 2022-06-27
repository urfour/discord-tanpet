import os
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DESCRIPTION = '''Bot de la guilde Tan pet de puicenss'''

bot = commands.Bot(command_prefix='!', description=DESCRIPTION)

@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user} (ID : {bot.user.id})')
    print('------')

@bot.command()
async def hello(ctx):
    await ctx.send(f'Salut {ctx.author.name} !')


@bot.command()
async def membres(ctx):
    to_print = ""
    for membre in ctx.guild.members:
        to_print += membre + " : 0 challenge(s) raté(s).\n"
    await ctx.send(to_print)

if __name__ == "__main__":
    bot.run(TOKEN)