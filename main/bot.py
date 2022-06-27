import os
import urllib.request
import datetime
import discord
import random
import pandas as pd

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
    if not os.path.exists('challs.csv'):
        print(f'Pas de fichier de challenges trouvé, merci de le générer !')
    else:
        bot.challs = pd.read_csv('challs.csv')

@bot.event
async def on_member_join(member):
    if member.id not in bot.challs['ID']:
        bot.challs.append({'ID':member.id, 'Name':member.name, 'Challenges':0}, ignore_index=True)
        print(f"Membre {member.name} (ID : {member.id} ajouté !")

class ChallengesCog(commands.Cog, name='Challenges'):
    def __init__(self, bot):
        self.bot = bot
        self.messages = [
            "Franchement t'abuses tu pourrais faire un effort...",
            "Évidemment c'est toujours le même !",
            "S U P E R encore toi",
            "Allez, encore un pour la route...",
            "On s'amuse avec toi décidément !"
        ]

    @commands.command()
    @commands.has_role('BG suprême')
    async def initchalls(self, ctx):
        """ Initialiser le compteur de challenges """
        members = [[member.id, member.name, 0] for member in ctx.guild.members]
        self.bot.challs = pd.DataFrame(members, columns=['ID', 'Name', 'Challenges'])
        self.bot.challs.to_csv('challs.csv')
        print("Compteur initialisé")
        await ctx.send(f"{ctx.author.mention} Compteur initialisé, essayez d'être bons quand même")

    @commands.command()
    async def infoall(self, ctx):
        """ Affiche les membres du serveur et leur nombre de challenges ratés """
        to_print = ""
        for membre in ctx.guild.members:
            if membre.id != self.bot.user.id:
                to_print += membre.name + " : " + self.bot.challs[self.bot.challs['ID'] == membre.id]['Challenges'][0] + " challenge(s) raté(s).\n"
        await ctx.send(to_print)

    @commands.command()
    async def info(self, ctx, member : discord.Member = None):
        """ Affiche le nombre de challenges ratés d'un joueur """
        if member is None:
            member = ctx.author

        await ctx.send(f"{member.name} a fait rater {self.bot.challs[self.bot.challs['ID'] == member.id]['Challenges'][0]} challenge(s) (le nullos)")

    @commands.command()
    async def addchall(self, ctx, member : discord.Member = None):
        """ Incrémente le compteur de challenges ratés (pas d'abus svp) """
        if member is None:
            member = ctx.author

        self.bot.challs[self.bot.challs['ID'] == member.id]['Challenges'] += 1
        await ctx.send(f"{ctx.author.mention} {self.messages[random.uniform(0, len(self.messages))]}")

class MiscCog(commands.Cog, name='Divers'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief="Dire bonjour (c'est important d'être poli)")
    async def hello(self, ctx):
        """ Dire bonjour (c'est important d'être poli) """
        await ctx.send(f'Salut {ctx.author.mention} !')
    
    @commands.command()
    async def almanax(self, ctx):
        """ Récupère l'Almanax du jour """
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
    bot.add_cog(ChallengesCog(bot))
    bot.add_cog(MiscCog(bot))
    bot.run(TOKEN)