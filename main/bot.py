import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DESCRIPTION = '''Bot de la guilde Tan pet de puicenss'''

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', description=DESCRIPTION, intents=intents)

@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user} (ID : {bot.user.id})')
    print('------')

@bot.command()
async def hello(ctx):
    await ctx.send(f'Salut {ctx.author.nick} !')

@bot.command()
async def help(ctx):
    commandes = "!hello : dire bonjour (important d'être poli)\n"
    commandes += "!membres : permet d'afficher les membres du serveur et leur nombre de challenges ratés\n"
    commandes += "C'est tout ! (pour l'instant)"
    await ctx.send(commandes)

@bot.command()
async def membres(ctx):
    to_print = ""
    for membre in ctx.guild.members:
        if membre.id != bot.user.id:
            to_print += membre.name + " : 0 challenge(s) raté(s).\n"
    await ctx.send(to_print)

if __name__ == "__main__":
    bot.run(TOKEN)