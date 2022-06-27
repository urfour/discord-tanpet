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

DATABASE_URL = os.environ["HEROKU_POSTGRESQL_CYAN_URL"].replace('postgres', 'postgresql')
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
    try:
        if engine.execute("SELECT * FROM challenges").fetchone() is not None:
            print(f'Base de données disponible !')
    except psycopg2.errors.UndefinedTable:
        print(f'Pas de fichier de challenges trouvé, merci de le générer !')

@bot.event
async def on_member_join(member):
    if member.id not in bot.challs['ID']:
        bot.challs.append({'discordid':member.id, 'name':member.name, 'challenges':0}, ignore_index=True)
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
        """ (Ré)Initialiser le compteur de challenges """
        members = [[member.id, member.name, 0] for member in ctx.guild.members if bot.user.id != member.id]
        self.bot.challs = pd.DataFrame(members, columns=['discordid', 'name', 'challenges'])
        self.bot.challs.to_sql('challenges', con=engine, if_exists='replace')
        print("Compteur (ré)initialisé")
        await ctx.send(f"{ctx.author.mention} Compteur (ré)initialisé, essayez d'être bons quand même")

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
        for _, row in results.iterrows():
                to_print += f"{row['name']} : {row['challenges']} challenge(s) raté(s)\n"
        await ctx.send(to_print)

    @commands.command()
    async def info(self, ctx, member : discord.Member = None):
        """ Affiche le nombre de challenges ratés d'un joueur """
        if member is None:
            member = ctx.author

        con = psycopg2.connect(DATABASE_URL)
        cur = con.cursor()
        query = f"""SELECT * 
                    FROM challenges 
                    WHERE discordid = {member.id}"""
        results = pd.read_sql(query, con)
        if results.iloc[0]['challenges'] == 0:
            await ctx.send(f"{member.nick} n'a fait rater **aucun** challenge (quel bg !)")
        else:
            await ctx.send(f"{member.nick} a fait rater {results.iloc[0]['challenges']} challenge(s) (le nullos)")

    @commands.command()
    async def addchall(self, ctx, member : discord.Member = None):
        """ Incrémente le compteur de challenges ratés (pas d'abus svp) """
        if member is None:
            member = ctx.author

        con = psycopg2.connect(DATABASE_URL)
        cur = con.cursor()
        query = f"""SELECT challenges 
                    FROM challenges 
                    WHERE discordid = {member.id}"""
        challenges = pd.read_sql(query, con)
        print("challenges")
        print(challenges)
        print("challenges loc : ")
        print(challenges.iloc[0].values)
        query2 = f"""UPDATE challenges 
                    SET challenges = {(int(challenges.iloc[0].values[0]) + 1)} 
                    WHERE discordid = {member.id}"""
        results = pd.read_sql(query2, con)
        print(results)
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