import random
import nextcord
import locale
import requests
import psycopg2

locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

from math import ceil
from bs4 import BeautifulSoup
from nextcord import ButtonStyle, Embed, Color, Interaction
from nextcord.ext import commands
from nextcord.ui import Button, View
from dotenv import load_dotenv
from os import getenv

load_dotenv()

TOKEN = getenv("DISCORD_TOKEN")
DATABASE_URL = getenv('DATABASE_URL')
DESCRIPTION = '''Bot de la guilde Tan pet de puicenss'''

FAILED_MESSAGES = [
    "Franchement t'abuses tu pourrais faire un effort...",
    "Évidemment c'est toujours le même !",
    "S U P E R encore toi",
    "Allez, encore un pour la route...",
    "On s'amuse avec toi décidément !"
    ]
    
intents = nextcord.Intents.all()
bot = commands.Bot(description=DESCRIPTION, intents=intents)
con = psycopg2.connect(DATABASE_URL)

@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user} (ID : {bot.user.id})')
    print('------')

@bot.event
async def on_member_join(member):
    if not member.bot:
        cur = con.cursor()
        query = """ INSERT INTO members 
                    (discordid, name)
                    VALUES (%s, %s)
                    ON CONFLICT (discordid) DO NOTHING"""
        cur.execute(query, (member.id, member.name))
        con.commit()
        print(f"{member.display_name} a été ajouté à la base de données.")

@bot.slash_command(default_member_permissions=8)
async def reset_challs_ref(interaction : Interaction):
    """ (Ré)Initialiser la table de référence des challenges """
    await interaction.response.defer(ephemeral=True)
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
    await interaction.followup.send("Les challenges ont bien été ajoutés dans la base de données !", ephemeral=True)

@bot.slash_command(default_member_permissions=8)
async def setup_count(interaction : Interaction):
    """ (Ré)Initialiser le compteur de challenges """
    await interaction.response.defer(ephemeral=True)
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

        cur.execute(""" DROP TABLE IF EXISTS members CASCADE """)
        cur.execute(""" CREATE TABLE members (
                            id SERIAL NOT NULL ,
                            discordid VARCHAR(100) NOT NULL UNIQUE,
                            name VARCHAR(100),
                            PRIMARY KEY (id, discordid)
                        ) """)
        con.commit()
        members = [(member.id, member.name) for member in interaction.guild.members if bot.user.id != member.id and not member.bot]
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
    await interaction.followup.send("Tout est prêt, essayez d'être bons quand même", ephemeral=True)

@bot.slash_command()
async def remove_last_chall(interaction : Interaction, member : nextcord.Member = None):
    """ Supprime l'entrée du dernier challenge ajouté """

    if member is None:
        member = interaction.user

    cur = con.cursor()
    query = """ DELETE FROM challenges
                WHERE id = (SELECT MAX(id) FROM challenges) """
    cur.execute(query)
    con.commit()
    await interaction.response.send_message("Le dernier challenge ajouté au joueur a bien été retiré, désolé pour l'erreur !")

@bot.slash_command()
async def info(interaction : Interaction, member : nextcord.Member = None):
    """ Affiche le nombre de challenges ratés d'un joueur """

    async def share_callback(interaction : Interaction):
        nonlocal embed
        await interaction.response.send_message(embed=embed)

    share_button = Button(label="Partager", style=ButtonStyle.blurple)
    share_button.callback = share_callback

    my_view = View(timeout=600)
    my_view.add_item(share_button)

    if member is None:
        member = interaction.user

    cur = con.cursor()
    query = f""" SELECT name, COUNT(*) 
                FROM challenges, challenges_reference
                WHERE discordid = '{member.id}'
                AND challenges.challengeid = challenges_reference.id
                GROUP BY name 
                ORDER BY 2 DESC, name ASC """
    cur.execute(query)
    challs = cur.fetchall()

    if len(challs) == 0:
        await interaction.response.send_message(f"{member.display_name} n'a fait rater **aucun** challenge (quel bg !)", ephemeral=True)
    else:
        embed = Embed(title="Totalité des challenges ratés", color=Color.red())

        if len(challs) > 25:
            nb_embed = len(challs) / 25
        else:
            nb_embed = 1

        for i in range(ceil(nb_embed)):
            if i == 0:
                embed = Embed(title=f"Challenges ratés par {member.display_name}", color=Color.red())
            else:
                embed = Embed(color=Color.red())
            for j, row in enumerate(challs[i*25:(i+1)*25]):
                if i == 0 and j == 0:
                    name = ':first_place: ' + row[0]
                elif i == 0 and j == 1:
                    name = ':second_place: ' + row[0]
                elif i == 0 and j == 2:
                    name = ':third_place: ' + row[0]
                else:
                    name = row[0]
                embed.add_field(name=name, value=f"{row[1]} échec{'s' if row[1] != 1 else ''}", inline=True)
            await interaction.response.send_message(embed=embed, view=my_view, ephemeral=True)

@bot.slash_command()
async def info_chall(interaction : Interaction, challenge : str):
    """ Affiche les informations sur un challenge raté """

    async def share_callback(interaction : Interaction):
        nonlocal embed
        await interaction.response.send_message(embed=embed)

    share_button = Button(label="Partager", style=ButtonStyle.blurple)
    share_button.callback = share_callback

    my_view = View(timeout=600)
    my_view.add_item(share_button)

    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    query = """ SELECT id FROM challenges_reference
                WHERE UPPER(name) LIKE UPPER(%s) """
    cur.execute(query, (challenge,))
    chall_exist = cur.fetchone()
    if chall_exist is None:
        await interaction.response.send_message("Le challenge n'existe pas.", ephemeral=True)
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
            await interaction.response.send_message("Le challenge n'a pas été raté pour l'instant :sunglasses:", ephemeral=True)
        else:
            cur.execute(""" SELECT image
                            FROM challenges_reference
                            WHERE UPPER(challenges_reference.name) LIKE UPPER(%s) """, (challenge,))
            image = cur.fetchone()
            embed = Embed(
                title=challenge,
                description='Challenges ratés',
                color=Color.gold(),
            )
            embed.set_thumbnail(url=image[0])
            for chall in challs:
                embed.add_field(name=chall[0], value=f'{chall[1]} fois')
            await interaction.response.send_message(embed=embed, view=my_view, ephemeral=True)       

@bot.slash_command()
async def info_all(interaction : Interaction):
    """ Affiche le nombre de challenges ratés de tout le monde """

    async def share_callback(interaction : Interaction):
        nonlocal embed
        await interaction.response.send_message(embed=embed)

    share_button = Button(label="Partager", style=ButtonStyle.blurple)
    share_button.callback = share_callback

    my_view = View(timeout=600)
    my_view.add_item(share_button)

    cur = con.cursor()
    query = f"""SELECT name, COUNT(*)
                FROM challenges, members
                WHERE challenges.discordid = members.discordid
                GROUP BY name
                ORDER BY 2 DESC, name ASC """
    cur.execute(query)
    challs = cur.fetchall()
    if len(challs) == 0:
        await interaction.response.send_message(
            content="Félicitations, personne n'a raté de challenge :sunglasses: (pour l'instant...)", 
            view=my_view, 
            ephemeral=True
        )
    else:
        if len(challs) > 25:
            nb_embed = len(challs) / 25
        else:
            nb_embed = 1

        for i in range(ceil(nb_embed)):
            if i == 0:
                embed = Embed(title="Nombre de challenges ratés", color=Color.purple())
            else:
                embed = Embed(color=Color.purple())
            for j, row in enumerate(challs[i*25:(i+1)*25]):
                user = nextcord.utils.get(interaction.guild.members, name=row[0])
                if i == 0 and j == 0:
                    name = ':first_place: ' + user.display_name
                elif i == 0 and j == 1:
                    name = ':second_place: ' + user.display_name
                elif i == 0 and j == 2:
                    name = ':third_place: ' + user.display_name
                else:
                    name = user.display_name
                embed.add_field(name=name, value=f"{row[1]} challenge{'s' if row[1] != 1 else ''}", inline=True)
            await interaction.response.send_message(embed=embed, view=my_view, ephemeral=True)         

@bot.slash_command()
async def add_chall(interaction : Interaction, challenge : str, member : nextcord.Member = None):
    """ Ajoute un challenge raté (pas d'abus svp) """

    if member is None:
        member = interaction.user

    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    query2 = """ SELECT id
                FROM challenges_reference
                WHERE UPPER(name) LIKE UPPER(%s) """
    cur.execute(query2, (challenge,))
    con.commit()
    row = cur.fetchone()
    if row is None:
        await interaction.response.send_message("Ce challenge n'existe pas, ou celui-ci n'a pas été renseigné.", ephemeral=True)
    else:
        challenge_id = row[0]
        
        query = """ INSERT INTO challenges(discordid, challengeid)
                    VALUES (%s, %s)"""
        cur.execute(query, (str(member.id), challenge_id))
        con.commit()
        embed = Embed(
            title='Challenge raté',
            color=Color.red()
        )
        embed.add_field(name=challenge, value=f"{member.mention} {random.choice(FAILED_MESSAGES)}")
        await interaction.response.send_message(embed=embed)

@bot.slash_command()
async def challs(interaction : Interaction):
    """ Affiche tous les challenges existants """
    cur = con.cursor()
    query = """ SELECT name, description
                FROM challenges_reference """
    cur.execute(query)
    con.commit()

    challs = cur.fetchall()
    embed = Embed(title="Challenges", description="Totalité des challenges disponibles sur Dofus", color=Color.orange())
    embed.set_thumbnail(url=f'https://image.over-blog.com/5ZW7J-uV9A9TuPXKCO3m2LPf7VE=/filters:no_upscale()/image%2F1215535%2F20211125%2Fob_475eb1_cheat-des-devs.png')

    if len(challs) > 25:
        nb_embed = len(challs) / 25
    else:
        nb_embed = 1

    for i in range(ceil(nb_embed)):
        if i == 0:
            embed = Embed(title="Challenges", description="Totalité des challenges disponibles sur Dofus", color=Color.orange())
        else:
            embed = Embed(color=Color.orange())
        for l in challs[i*25:(i+1)*25]:
            embed.add_field(name=l[0], value=l[1], inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

if __name__ == '__main__':
    bot.run(TOKEN)