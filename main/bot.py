from math import ceil
import os
import datetime
import discord
import random
import requests
import psycopg2
import locale

locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

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

async def send_embed(ctx, embed):

    try:
        await ctx.send(embed=embed)
    except discord.errors.Forbidden:
        try:
            await ctx.send("Erreur d'envoi, merci de vérifier les permissions du bot !")
        except discord.errors.Forbidden:
            await ctx.author.send(
                f"Ah c'est marrant mais je peux pas envoyer de message sur le canal {ctx.channel.name} de {ctx.guild.name}...\n"
                f"Tu peux le dire à UrFour s'il te plaît ? :slight_smile: ", embed=embed)

@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user} (ID : {bot.user.id})')
    print('------')

@bot.event
async def on_member_join(member):
    if not member.bot:
        con = psycopg2.connect(DATABASE_URL)
        cur = con.cursor()
        query = """ INSERT INTO members 
                    (discordid, name)
                    VALUES (%s, %s)
                    ON CONFLICT (discordid) DO NOTHING"""
        cur.execute(query, (member.id, member.name))
        con.commit()
        print(f"{member.name} a été ajouté à la base de données.")

class Help(commands.Cog, name='Aide'):
    """
    Envoie ce message d'aide
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    # @commands.bot_has_permissions(add_reactions=True,embed_links=True)
    async def help(self, ctx, *input):
        """Affiche tous les modules"""
	
	# !SET THOSE VARIABLES TO MAKE THE COG FUNCTIONAL!
        prefix = '!'
        version = 'v1'
        
        # setting owner name - if you don't wanna be mentioned remove line 49-60 and adjust help text (line 88) 
        owner = '149195176093548544'

        # checks if cog parameter was given
        # if not: sending all modules and commands not associated with a cog
        if not input:
            # checks if owner is on this server - used to 'tag' owner
            try:
                owner = ctx.guild.get_member(owner).mention

            except AttributeError as e:
                owner = owner

            # starting to build embed
            emb = discord.Embed(title='Commandes et modules', color=discord.Color.blue(),
                                description=f'`{prefix}help <module>` pour avoir plus d\'information sur ce module '
                                            f':smiley:\n')

            # iterating trough cogs, gathering descriptions
            cogs_desc = ''
            for cog in self.bot.cogs:
                cogs_desc += f'`{cog}` {self.bot.cogs[cog].__doc__}\n'

            # adding 'list' of cogs to embed
            emb.add_field(name='Modules', value=cogs_desc, inline=False)

            # integrating trough uncategorized commands
            commands_desc = ''
            for command in self.bot.walk_commands():
                # if cog not in a cog
                # listing command if cog name is None and command isn't hidden
                if not command.cog_name and not command.hidden:
                    commands_desc += f'{command.name} - {command.help}\n'

            # adding those commands to embed
            if commands_desc:
                emb.add_field(name='Autre', value=commands_desc, inline=False)

            # setting information about author
            emb.add_field(name="A propos", value=f"Bot de la guilde qui monte malgré le silence des médias")
            emb.set_footer(text=f"Version actuelle du bot : {version}")

        # block called when one cog-name is given
        # trying to find matching cog and it's commands
        elif len(input) == 1:

            # iterating trough cogs
            for cog in self.bot.cogs:
                # check if cog is the matching one
                if cog.lower() == input[0].lower():

                    # making title - getting description from doc-string below class
                    emb = discord.Embed(title=f'{cog} - Commandes', description=self.bot.cogs[cog].__doc__,
                                        color=discord.Color.green())

                    # getting commands from cog
                    for command in self.bot.get_cog(cog).get_commands():
                        # if cog is not hidden
                        if not command.hidden:
                            emb.add_field(name=f"`{prefix}{command.name}`", value=command.help, inline=False)
                    # found cog - breaking loop
                    break

            # if input not found
            # yes, for-loops have an else statement, it's called when no 'break' was issued
            else:
                emb = discord.Embed(title="wtf",
                                    description=f"Désolé mais le module `{input[0]}` n'existe pas :scream:",
                                    color=discord.Color.orange())

        # too many cogs requested - only one at a time allowed
        elif len(input) > 1:
            emb = discord.Embed(title="That's too much.",
                                description="Please request only one module at once :sweat_smile:",
                                color=discord.Color.orange())

        else:
            emb = discord.Embed(title="It's a magical place.",
                                description="I don't know how you got here. But I didn't see this coming at all.\n"
                                            "Would you please be so kind to report that issue to me on github?\n"
                                            "https://github.com/nonchris/discord-fury/issues\n"
                                            "Thank you! ~Chris",
                                color=discord.Color.red())

        # sending reply embed using our own function defined above
        await send_embed(ctx, emb)

class ChallengesCog(commands.Cog, name='Challenges'):
    """
    Informations concernant les challenges échoués
    """
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
    async def reset_challs_ref(self, ctx):
        """ (Ré)Initialiser la table de référence des challenges """
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
                (
                    tr[0].get_text().strip(), 
                    tr[1].get_text().strip(),
                    url.rsplit('/', 2)[0] + tr[3].find('img')['src'].split('..')[1]
                )
            )
        con = psycopg2.connect(DATABASE_URL)
        cur = con.cursor()
        cur.execute(""" DROP TABLE IF EXISTS challenges_reference CASCADE """)
        cur.execute(""" CREATE TABLE challenges_reference (
                            id SERIAL NOT NULL PRIMARY KEY,
                            name VARCHAR(50),
                            description VARCHAR(300),
                            image VARCHAR(100)
                        ) """)
        query = """ INSERT INTO challenges_reference(name, description, image)
                        VALUES (%s, %s, %s) """
        cur.executemany(query, challenges_dict)
        con.commit()
        await ctx.send(f"{ctx.author.mention} Les challenges ont bien été ajoutés dans la base de données !")

    @commands.command()
    @commands.has_role('BG suprême')
    async def setup(self, ctx):
        """ (Ré)Initialiser le compteur de challenges """
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
                (
                    tr[0].get_text().strip(), 
                    tr[1].get_text().strip(),
                    url.rsplit('/', 2)[0] + tr[3].find('img')['src'].split('..')[1]
                )
            )
        con = psycopg2.connect(DATABASE_URL)
        cur = con.cursor()
        cur.execute(""" DROP TABLE IF EXISTS challenges_reference CASCADE """)
        cur.execute(""" CREATE TABLE challenges_reference (
                            id SERIAL NOT NULL PRIMARY KEY,
                            name VARCHAR(50),
                            description VARCHAR(300),
                            image VARCHAR(100)
                        ) """)
        query = """ INSERT INTO challenges_reference(name, description)
                        VALUES (%s, %s) """
        cur.executemany(query, challenges_dict)
        con.commit()
        await ctx.send(f"{ctx.author.mention} Les challenges ont bien été ajoutés dans la base de données !")

        cur.execute(""" DROP TABLE IF EXISTS members CASCADE """)
        cur.execute(""" CREATE TABLE members (
                            id SERIAL NOT NULL ,
                            discordid VARCHAR(100) NOT NULL UNIQUE,
                            name VARCHAR(100),
                            PRIMARY KEY (id, discordid)
                        ) """)
        con.commit()
        members = [(member.id, member.name) for member in ctx.guild.members if bot.user.id != member.id and not member.bot]
        query = """ INSERT INTO members(discordid, name)
                    VALUES(%s, %s) """
        cur.executemany(query, members)

        query = """ DROP TABLE IF EXISTS challenges """
        cur.execute(query)
        query2 = """ CREATE TABLE challenges (
                    id SERIAL NOT NULL,
                    discordid VARCHAR(100),
                    challengeid INT,
                    PRIMARY KEY(id),
                    CONSTRAINT fk_discordid
                        FOREIGN KEY(discordid)
                            REFERENCES members(discordid),
                    CONSTRAINT fk_challengeid
                        FOREIGN KEY(challengeid)
                            REFERENCES challenges_reference(id) 
                    ) """
        cur.execute(query2)
        con.commit()        

        print("Tables (ré)initialisées")
        await ctx.send(f"{ctx.author.mention} Tout est prêt, essayez d'être bons quand même")

    @commands.command()
    @commands.has_role('BG suprême')
    async def get_chall_id(self, ctx, challenge : str):
        """ Récupère l'id d'un challenge """

        if challenge is None:
            await ctx.send(f"La syntaxe de la commmande est incorrecte, merci de réessayer.")
        else:
            con = psycopg2.connect(DATABASE_URL)
            cur = con.cursor()
            query2 = """ SELECT id
                        FROM challenges_reference
                        WHERE UPPER(name) LIKE UPPER(%s) """
            cur.execute(query2, (challenge,))
            con.commit()
            row = cur.fetchone()
            if row is None:
                await ctx.send("Ce challenge n'existe pas.")
            else:
                await ctx.send(row[0])

    @commands.command()
    @commands.has_role('BG suprême')
    async def remove_last_chall(self, ctx, member : discord.Member):
        """ Supprime l'entrée du dernier challenge ajouté """

        if member is None:
            member = ctx.author

        con = psycopg2.connect(DATABASE_URL)
        cur = con.cursor()
        query = """ DELETE FROM challenges
                    WHERE id = (SELECT MAX(id) FROM challenges) """
        cur.execute(query)
        con.commit()
        row = cur.fetchone()
        if row is None:
            await ctx.send("Ce challenge n'existe pas, ou celui-ci n'a pas été renseigné.")
        else:
            await ctx.send(f"Le dernier challenge ajouté au joueur a bien été retiré, désolé pour l'erreur !")

    @commands.command()
    async def challs(self, ctx):
        """ Affiche tous les challenges existants """
        user = await self.bot.fetch_user(ctx.author.id)

        con = psycopg2.connect(DATABASE_URL)
        cur = con.cursor()
        query = """ SELECT name, description
                    FROM challenges_reference """
        cur.execute(query)
        con.commit()

        challs = cur.fetchall()
        embed = discord.Embed(title="Challenges", description="Totalité des challenges disponibles sur Dofus", color=discord.Color.orange())
        embed.set_thumbnail(url=f'https://image.over-blog.com/5ZW7J-uV9A9TuPXKCO3m2LPf7VE=/filters:no_upscale()/image%2F1215535%2F20211125%2Fob_475eb1_cheat-des-devs.png')

        if len(challs) > 25:
            nb_embed = len(challs) / 25
        else:
            nb_embed = 1

        for i in range(ceil(nb_embed)):
            if i == 0:
                embed = discord.Embed(title="Challenges", description="Totalité des challenges disponibles sur Dofus", color=discord.Color.orange())
            else:
                embed = discord.Embed(color=discord.Color.orange())
            for l in challs[i*25:(i+1)*25]:
                embed.add_field(name=l[0], value=l[1], inline=False)
            await user.send(embed=embed)

    @commands.command()
    async def info_all(self, ctx):
        """ Affiche le nombre de challenges ratés de tout le monde """

        con = psycopg2.connect(DATABASE_URL)
        cur = con.cursor()
        query = f"""SELECT name, COUNT(*)
                    FROM challenges, members
                    WHERE challenges.discordid = members.discordid
                    GROUP BY name
                    ORDER BY 2 DESC, name ASC """
        cur.execute(query)
        challs = cur.fetchall()
        if len(challs) == 0:
            await ctx.send("Félicitations, personne n'a raté de challenge :sunglasses: (pour l'instant...)")
        else:
            to_print = ""
            for row in challs:
                if row[1] == 1:
                    to_print += f"{row[0]} : {row[1]} challenge raté\n"
                else:
                    to_print += f"{row[0]} : {row[1]} challenge(s) raté(s)\n"
            await ctx.send(to_print)

    @commands.command()
    async def challs_missed(self, ctx):
        """ Affiche les challenges les plus ratés """

        con = psycopg2.connect(DATABASE_URL)
        cur = con.cursor()
        query = f"""SELECT name, COUNT(*) as nb
                    FROM challenges, challenges_reference
                    WHERE challenges.challengeid = challenges_reference.id
                    GROUP BY name
                    ORDER BY 2 DESC, name ASC """
        cur.execute(query)
        challs = cur.fetchall()
        if len(challs) == 0:
            await ctx.send("Félicitations, personne n'a raté de challenge :sunglasses: (pour l'instant...)")
        else:
            embed = discord.Embed(title="Challenges", description="Totalité des challenges ratés", color=discord.Color.red())

            if len(challs) > 25:
                nb_embed = len(challs) / 25
            else:
                nb_embed = 1

            for i in range(ceil(nb_embed)):
                if i == 0:
                    embed = discord.Embed(title="Challenges", description="Totalité des challenges ratés", color=discord.Color.red())
                else:
                    embed = discord.Embed(color=discord.Color.red())
                for l in challs[i*25:(i+1)*25]:
                    if l[1] == 1:
                        embed.add_field(name=l[0], value=f"{l[1]} échec", inline=True)
                    else:
                        embed.add_field(name=l[0], value=f"{l[1]} échec(s)", inline=True)
                await ctx.send(embed=embed)

    @commands.command()
    async def info(self, ctx, member : discord.Member = None):
        """ Affiche le nombre de challenges ratés d'un joueur """

        if member is None:
            member = ctx.author

        con = psycopg2.connect(DATABASE_URL)
        cur = con.cursor()
        query = f""" SELECT name, COUNT(*) 
                    FROM challenges, challenges_reference
                    WHERE discordid = '{member.id}'
                    AND challenges.challengeid = challenges_reference.id
                    GROUP BY name 
                    ORDER BY 2 DESC, name ASC """
        cur.execute(query)
        challs = cur.fetchall()
        challenges_count = 0
        to_print = ""
        if len(challs) == 0:
            await ctx.send(f"{member.nick} n'a fait rater **aucun** challenge (quel bg !)")
        else:
            for chall in challs:
                to_print += f"- **{chall[1]}** fois le challenge **{chall[0]}**\n"
                challenges_count += chall[1]
            if challenges_count == 1:
                challs_missed = "challenge"
            else:
                challs_missed = "challenge(s)"
            to_print = f"{member.nick} a fait rater **{challenges_count}** {challs_missed} :\n" + to_print
            await ctx.send(to_print)

    @info.error
    async def info_error(self, ctx, error):
        if isinstance(error, commands.MemberNotFound):
            await ctx.send("Merci de préciser le membre pour lequel vous souhaitez connaître les challenges ratés.")

    @commands.command()
    async def info_chall(self, ctx, challenge : str):
        """ Affiche les informations sur un challenge raté """

        if challenge is None:
            await ctx.send("Sinon si tu me dis de quel challenge il s'agit ce serait plus simple...")
        else:
            con = psycopg2.connect(DATABASE_URL)
            cur = con.cursor()
            query = """ SELECT id FROM challenges_reference
                        WHERE UPPER(name) LIKE UPPER(%s) """
            cur.execute(query, (challenge,))
            chall_exist = cur.fetchone()
            if chall_exist is None:
                await ctx.send("Le challenge n'existe pas.")
            else:
                query = """ SELECT members.name, COUNT(*)
                            FROM challenges, challenges_reference, members
                            WHERE UPPER(challenges_reference.name) LIKE UPPER(%s)
                            AND challenges.challengeid = challenges_reference.id
                            AND members.discordid = challenges.discordid
                            GROUP BY members.name 
                            ORDER BY 2 DESC, members.name ASC"""
                cur.execute(query, (challenge,))
                challs = cur.fetchall()
                if len(challs) == 0:
                    await ctx.send("Le challenge n'a pas été raté pour l'instant :sunglasses:")
                else:
                    cur.execute(""" SELECT image
                                    FROM challenges_reference
                                    WHERE UPPER(challenges_reference.name) LIKE UPPER(%s) """, (challenge,))
                    image = cur.fetchone()
                    embed = discord.Embed(
                        title=challenge,
                        description='Challenges ratés :',
                        color=discord.Color.gold(),
                    )
                    embed.set_thumbnail(url=image[0])
                    for chall in challs:
                        embed.add_field(name=chall[0], value=f'{chall[1]} fois')
                    await send_embed(ctx, embed)                

    @commands.command()
    @commands.has_any_role('BG suprême', 'BGs originels')
    async def add_chall(self, ctx, member : discord.Member = None, challenge : str = None):
        """ Ajoute un challenge raté (pas d'abus svp) """

        if member is None:
            member = ctx.author

        con = psycopg2.connect(DATABASE_URL)
        cur = con.cursor()
        query2 = """ SELECT id
                    FROM challenges_reference
                    WHERE UPPER(name) LIKE UPPER(%s) """
        cur.execute(query2, (challenge,))
        con.commit()
        row = cur.fetchone()
        if row is None:
            await ctx.send("Ce challenge n'existe pas, ou celui-ci n'a pas été renseigné.")
        else:
            challenge_id = row[0]
            
            query = """ INSERT INTO challenges(discordid, challengeid)
                        VALUES (%s, %s)"""
            cur.execute(query, (str(member.id), challenge_id))
            con.commit()
            await ctx.send(f"{member.mention} {random.choice(self.messages)}")

class MiscCog(commands.Cog, name='Divers'):
    """ 
    Commandes diverses 
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_any_role('BG suprême')
    async def remove_bot(self, ctx):
        """ Retire les bots de la base de données """
        members = [member for member in ctx.guild.members if member.bot]
        if len(members) == 0:
            print("Aucun bot n'a été supprimé.")
        else:
            for member in members:
                con = psycopg2.connect(DATABASE_URL)
                cur = con.cursor()
                query = f""" DELETE FROM members
                            WHERE discordid = '{member.id}' """
                cur.execute(query)
            con.commit()
            await ctx.send(f"{ctx.author.mention} Les bots ont bien été supprimés de la base de données !")
            print("Bots supprimés de la base de données")

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
        page = requests.get(almanax_url).text
        soup = BeautifulSoup(page, 'html.parser')

        div = soup.find('div', {'class': 'more-infos-content'})
        
        embed = discord.Embed(
            title=f'Almanax du {today.strftime("%A %w %B %Y")}', 
            color=discord.Color.purple(),
            url=almanax_url
        )
        embed.set_thumbnail(url=div.find('img')['src'])
        embed.add_field(name='Ressource', value=div.find('p').getText().strip())

        await send_embed(ctx, embed)

if __name__ == "__main__":
    bot.remove_command('help')
    bot.add_cog(ChallengesCog(bot))
    bot.add_cog(MiscCog(bot))
    bot.add_cog(Help(bot))
    bot.run(TOKEN)