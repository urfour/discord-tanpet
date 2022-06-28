import os
import urllib.request
import datetime
import discord
import random
import pandas as pd
import requests
import psycopg2

from bs4 import BeautifulSoup
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

@bot.event
async def on_member_join(member):
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    query = """ INSERT INTO members 
                (discordid, name)
                VALUES (%s, %s)
                ON CONFLICT (discordid) DO NOTHING"""
    cur.execute(query, (member.id, member.name))
    con.commit()
    print(f"{member.name} a été ajouté à la base de données.")

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
    async def add_chall_references(self, ctx):
        """ Ajouter les noms des différents challenges dans la base de données """

        url = 'https://tofus.fr/fiches/challenge.php'
        challenges_page = requests.get(url)
        soup = BeautifulSoup(challenges_page.text, 'html.parser')
        table = soup.find('table')
        challenges = [row for row in table.find_all('tr')]
        challenges.pop(0)

        challenges_dict = []

        for row in challenges:
            tr = row.find_all('td')
            challenges_dict.append(
                {'name': tr[0].get_text(),
                'description': tr[1].get_text()
                }
            )
        df = pd.DataFrame.from_dict(challenges_dict)
        df.to_sql('challenges_reference', con=engine, if_exists='replace')
        await ctx.send(f"{ctx.author.mention} Les challenges ont bien été ajoutés dans la base de données !")

    @commands.command()
    @commands.has_role('BG suprême')
    async def init_challs(self, ctx):
        """ (Ré)Initialiser le compteur de challenges """

        con = psycopg2.connect(DATABASE_URL)
        cur = con.cursor()
        cur.execute(""" DROP TABLE IF EXISTS members """)
        con.commit()
        members = [[(i-1), member.id, member.name] for i, member in enumerate(ctx.guild.members) if bot.user.id != member.id]
        self.bot.challs = pd.DataFrame(members, columns=['id', 'discordid', 'name'])
        self.bot.challs.to_sql('members', con=engine, index_label='id', if_exists='replace')

        query = """ DROP TABLE IF EXISTS challenges """
        cur.execute(query)
        query2 = """ CREATE TABLE challenges (
                    id INT GENERATED ALWAYS AS IDENTITY,
                    discordid INT,
                    challengeid INT,
                    PRIMARY KEY(id),
                    CONSTRAINT fk_discordid
                        FOREIGN KEY(discordid)
                            REFERENCES members(discordid),
                    CONSTRAINT fk_challengeid
                        FOREIGN KEY(challengeid)
                            REFERENCES challenges_references(id) 
                    ) """
        cur.execute(query2)
        con.commit()        

        print("Compteur (ré)initialisé")
        await ctx.send(f"{ctx.author.mention} Compteur (ré)initialisé, essayez d'être bons quand même")

    @commands.command()
    @commands.has_role('BG suprême')
    async def get_chall_id(self, ctx, challenge : str):
        """ Récupère l'id d'un challenge """

        if challenge is None:
            await ctx.send(f"La syntaxe de la commmande est incorrecte, merci de réessayer.")
        else:
            con = psycopg2.connect(DATABASE_URL)
            cur = con.cursor()
            query2 = f""" SELECT id
                        FROM challenges_references
                        WHERE name LIKE {challenge} """
            cur.execute(query2)
            con.commit()
            print(cur)
            #await ctx.send(f"Le nombre de challenges ratés du joueur a été défini à {number}.")

    @commands.command()
    async def challs(self, ctx):
        """ Affiche tous les challenges existants """

        con = psycopg2.connect(DATABASE_URL)
        cur = con.cursor()
        query = """ SELECT *
                    FROM challenges_references """
        cur.execute(query)
        print(cur)

        to_print = ""
        for l in cur:
            to_print += f"{cur[1]} : {cur[2]}\n"
        
        con.commit()
        await ctx.send(to_print)

    @commands.command()
    async def info_all(self, ctx):
        """ Affiche les membres du serveur et leur nombre de challenges ratés """

        con = psycopg2.connect(DATABASE_URL)
        query = f"""SELECT *
                    FROM members
                    ORDER BY name ASC
                        """
        results = pd.read_sql(query, con)
        print("INFOALL")
        print(results)
        to_print = ""
        for _, row in results.iterrows():
                to_print += f"{row['name']}\n"
        await ctx.send(to_print)

    @commands.command()
    async def info(self, ctx, member : discord.Member = None):
        """ Affiche le nombre de challenges ratés d'un joueur """

        if member is None:
            member = ctx.author

        con = psycopg2.connect(DATABASE_URL)
        cur = con.cursor()
        query = f"""SELECT * 
                    FROM members 
                    WHERE discordid = {member.id}"""
        results = pd.read_sql(query, con)
        if results.iloc[0]['challenges'] == 0:
            await ctx.send(f"{member.nick} n'a fait rater **aucun** challenge (quel bg !)")
        else:
            await ctx.send(f"{member.nick} a fait rater {results.iloc[0]['challenges']} challenge(s) (le nullos)")

    @commands.command()
    @commands.has_role('BGs originels')
    async def add_chall(self, ctx, member : discord.Member = None, challenge : str = None):
        """ Incrémente le compteur de challenges ratés (pas d'abus svp) """
    
        if challenge is None:
            await ctx.send("Je n'ai pas compris quel est le challenge qui a été échoué, merci de réessayer.")
        else:
            if member is None:
                member = ctx.author

            con = psycopg2.connect(DATABASE_URL)
            cur = con.cursor()
            query = f""" SELECT challenges 
                        FROM members 
                        WHERE discordid = {member.id} """
            challenges = pd.read_sql(query, con)
            chall_value = str(int(challenges.iloc[0].values[0]) + 1)
            query2 = """ UPDATE members 
                        SET challenges = %s
                        WHERE discordid = %s """
            cur.execute(query2, (chall_value, member.id))
            con.commit()
            await ctx.send(f"{ctx.author.mention} {self.messages[random.randint(0, len(self.messages))]}")

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

        today = datetime.date.today()
        date = today.strftime("%Y-%m-%d")

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