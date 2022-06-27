import os
import urllib.request
import datetime
import discord
import random
import pandas as pd
import psycopg2
from sqlalchemy import create_engine

from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()

DATABASE_URL = os.getenv("HEROKU_POSTGRESQL_CYAN_URL")
TOKEN = os.getenv("DISCORD_TOKEN")
DESCRIPTION = '''Bot de la guilde Tan pet de puicenss'''

engine = create_engine(DATABASE_URL, echo=False)

intents = discord.Intents.default()
intents.members = True
    
bot = commands.Bot(command_prefix='!', description=DESCRIPTION, intents=intents)

@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user} (ID : {bot.user.id})')
    print('------')
    if engine.execute("SELECT * FROM challenges").fetchone() is None:
        print(f'Pas de fichier de challenges trouvé, merci de le générer !')

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
        self.bot.challs.set_index('ID', inplace=True)
        self.bot.challs.to_sql('challenges', con=engine, if_exists='append')
        print("Compteur initialisé")
        await ctx.send(f"{ctx.author.mention} Compteur initialisé, essayez d'être bons quand même")

    @commands.command()
    async def infoall(self, ctx):
        """ Affiche les membres du serveur et leur nombre de challenges ratés """
        con = psycopg2.connect(DATABASE_URL)
        cur = con.cursor()
        query = f"""SELECT *
                    FROM challenges
                        """

        results = pd.read_sql(query, con)
        print("INFOALL")
        print(results)
        to_print = ""
        for membre in ctx.guild.members:
            if membre.id != self.bot.user.id:
                to_print += membre.name + " : " + self.bot.challs.loc[str(membre.id)]['Challenges'] + " challenge(s) raté(s).\n"
        await ctx.send(to_print)

    @commands.command()
    async def info(self, ctx, member : discord.Member = None):
        """ Affiche le nombre de challenges ratés d'un joueur """
        if member is None:
            member = ctx.author

        await ctx.send(f"{member.name} a fait rater {self.bot.challs.loc[str(member.id)]['Challenges']} challenge(s) (le nullos)")

    @commands.command()
    async def addchall(self, ctx, member : discord.Member = None):
        """ Incrémente le compteur de challenges ratés (pas d'abus svp) """
        if member is None:
            member = ctx.author

        self.bot.challs[str(member.id)]['Challenges'] += 1
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