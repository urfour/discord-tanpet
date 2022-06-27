# This example requires the 'members' and 'message_content' privileged intents to function.

import discord
from discord.ext import commands

description = '''Bot de la guilde Tan pet de puicenss'''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', description=description, intents=intents)

@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user} (ID : {bot.user.id})')
    print('------')

@bot.command
async def hello(ctx):
    await ctx.send(f'Salut {ctx.author.name} !')

bot.run('token')