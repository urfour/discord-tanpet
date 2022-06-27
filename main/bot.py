import os
import urllib.request
import datetime
import discord

from dotenv import load_dotenv
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
    """ Dire bonjour (c'est important d'être poli)"""
    await ctx.send(f'Salut {ctx.author.nick} !')

@bot.command()
async def membres(ctx):
    """ Permet d'afficher les membres du serveur et leur nombre de challenges ratés"""
    to_print = ""
    for membre in ctx.guild.members:
        if membre.id != bot.user.id:
            to_print += membre.name + " : 0 challenge(s) raté(s).\n"
    await ctx.send(to_print)

@bot.command()
async def almanax(ctx):
    """ Récupère l'Almanax du jour"""
    # Get today date
    today = datetime.date.today()
    date = today.strftime("%Y-%m-%d")

    # Get corresponding Almanax
    almanax_url = "http://www.krosmoz.com/fr/almanax/" + date
    fp = urllib.request.urlopen(almanax_url)
    html = fp.read()
    text = html.decode("utf8")
    fp.close()
    for line in text.split('\n'):
        if 'Récupérer' in line:
            offrande = line
            break

    fp.close()
    offrande = offrande[15:-17]
    offrande += "\nhttps://www.krosmoz.com/fr/almanax"
    await ctx.send(offrande)

if __name__ == "__main__":
    bot.run(TOKEN)