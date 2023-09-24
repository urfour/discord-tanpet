import random
import nextcord
import locale
import requests
import psycopg2
import pandas as pd

locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

from math import ceil
from datetime import time
from psycopg2.extras import execute_batch
from nextcord import ButtonStyle, Embed, Color, Interaction
from nextcord.ext import commands, tasks
from nextcord.ui import Button, View, Select
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
all_challenges = []

def get_challenges(page_nb):
    dropdown_options = [nextcord.SelectOption(label=chall['name'], value=str(i)) for i, chall in all_challenges.iloc[page_nb*25:(page_nb+1)*25].iterrows()]
    dropdown = Select(placeholder='Choisissez le challenge à afficher', options=dropdown_options)
    return dropdown

@bot.event
async def on_ready():
    global all_challenges
    cur = con.cursor()
    query = """ SELECT name, description, image
                FROM challenges_reference """
    cur.execute(query)
    con.commit()
    all_challenges = pd.DataFrame(cur.fetchall(), columns=['name', 'description', 'image'])
    challenges_reminder.start()
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

@tasks.loop(time=[time(hour = 8), time(hour = 16)])
async def challenges_reminder():
    print('Sending challenges reminder')
    cur = con.cursor()
    query = f"""SELECT name, COUNT(*)
                FROM challenges, members
                WHERE challenges.discordid = members.discordid
                GROUP BY name
                ORDER BY 2 DESC, name ASC """
    cur.execute(query)
    challs = cur.fetchall()
    if len(challs) == 0:
        await bot.get_channel(990910850950889512).send(
            content="@here Félicitations, personne n'a raté de challenge :sunglasses: (pour l'instant...)", 
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
                user = nextcord.utils.get(bot.guild.members, name=row[0])
                if i == 0 and j == 0:
                    name = ':first_place: ' + user.display_name
                elif i == 0 and j == 1:
                    name = ':second_place: ' + user.display_name
                elif i == 0 and j == 2:
                    name = ':third_place: ' + user.display_name
                else:
                    name = user.display_name
                embed.add_field(name=name, value=f"{row[1]} challenge{'s' if row[1] != 1 else ''}", inline=True)
            await bot.get_channel(990910850950889512).send('@here', embed=embed)       

@bot.slash_command(default_member_permissions=8)
async def reset_challs_ref(interaction : Interaction):
    """ (Ré)Initialiser la table de référence des challenges """
    await interaction.response.defer(ephemeral=True)
    first_challenges = requests.get('https://api.dofusdb.fr/challenges?$skip=0&$sort[slug.fr]=1&$limit=50&categoryId[]=1&categoryId[]=4&iconId[$ne]=0&lang=fr').json()
    second_challenges = requests.get('https://api.dofusdb.fr/challenges?$skip=50&$sort[slug.fr]=1&$limit=50&categoryId[]=1&categoryId[]=4&iconId[$ne]=0&lang=fr').json()
    challenges = []
    for challenge in first_challenges['data']:
        challenges.append(
            [
                challenge['name']['fr'],
                challenge['description']['fr'],
                f"https://api.dofusdb.fr/img/challenges/{challenge['id']}.png"
            ]
        )
    for challenge in second_challenges['data']:
        challenges.append(
            [
                challenge['name']['fr'],
                challenge['description']['fr'],
                f"https://api.dofusdb.fr/img/challenges/{challenge['id']}.png"
            ]
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
    execute_batch(cur, query, challenges)
    con.commit()
    await interaction.followup.send("Les challenges ont bien été ajoutés dans la base de données !", ephemeral=True)

@bot.slash_command(default_member_permissions=8)
async def setup_count(interaction : Interaction):
    """ (Ré)Initialiser le compteur de challenges """
    await interaction.response.defer(ephemeral=True)
    first_challenges = requests.get('https://api.dofusdb.fr/challenges?$skip=0&$sort[slug.fr]=1&$limit=50&categoryId[]=1&categoryId[]=4&iconId[$ne]=0&lang=fr').json()
    second_challenges = requests.get('https://api.dofusdb.fr/challenges?$skip=50&$sort[slug.fr]=1&$limit=50&categoryId[]=1&categoryId[]=4&iconId[$ne]=0&lang=fr').json()
    challenges = []
    for challenge in first_challenges['data']:
        challenges.append(
            [
                challenge['name']['fr'],
                challenge['description']['fr'],
                f"https://api.dofusdb.fr/img/challenges/{challenge['id']}.png"
            ]
        )
    for challenge in second_challenges['data']:
        challenges.append(
            [
                challenge['name']['fr'],
                challenge['description']['fr'],
                f"https://api.dofusdb.fr/img/challenges/{challenge['id']}.png"
            ]
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
    execute_batch(cur, query, challenges)
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
    current_page = 0
    async def dropdown_callback(interaction : nextcord.Interaction):
        selected_option = -1
        for option in dropdown.options:
            if option.value == dropdown.values[0]:
                selected_option = option

        dropdown_view = View(timeout=180)
        embed = Embed(title=selected_option.label, description=all_challenges.iloc[int(selected_option.value)]['description'], color=Color.orange())
        embed.set_thumbnail(all_challenges.iloc[int(selected_option.value)]['image'])
        await interaction.response.send_message(embed=embed, view=dropdown_view, ephemeral=True)

    async def previous_callback(interaction):
        nonlocal current_page, sent_msg, dropdown
        if current_page > 0:
            current_page -= 1
            my_view.remove_item(dropdown)
            dropdown = get_challenges(page_nb=current_page)
            dropdown.callback = dropdown_callback
            my_view.add_item(dropdown)
            await sent_msg.edit(f"Page {current_page+1}", view=my_view)

    async def next_callback(interaction):
        nonlocal current_page, sent_msg, dropdown
        current_page += 1
        my_view.remove_item(dropdown)
        dropdown = get_challenges(page_nb=current_page)
        dropdown.callback = dropdown_callback
        my_view.add_item(dropdown)
        await sent_msg.edit(f"Page {current_page+1}", view=my_view)

    previous_button = Button(label="<", style=ButtonStyle.blurple)
    previous_button.callback = previous_callback

    next_button = Button(label=">", style=ButtonStyle.blurple)
    next_button.callback = next_callback
    
    dropdown = get_challenges(page_nb=0)
    dropdown.callback = dropdown_callback

    my_view = View(timeout=600)
    my_view.add_item(dropdown)
    my_view.add_item(previous_button)
    my_view.add_item(next_button)
    sent_msg = await interaction.response.send_message('Page 1', view=my_view, ephemeral=True)

if __name__ == '__main__':
    bot.run(TOKEN)