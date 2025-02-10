# bot_entretenimiento.py

import discord
from discord.ext import commands
import psycopg2
import psycopg2.extras
import os
import random
import unicodedata

######################################
# CONFIGURACIÓN: IDs y Servidor
######################################
OWNER_ID = 1336609089656197171  # Reemplaza con tu Discord ID

######################################
# CONEXIÓN A LA BASE DE DATOS POSTGRESQL
######################################
DATABASE_URL = os.environ.get("DATABASE_URL")  # La variable de entorno en Render
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True

def init_db():
    with conn.cursor() as cur:
        # Tabla de chistes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS jokes (
                id SERIAL PRIMARY KEY,
                joke_text TEXT NOT NULL
            )
        """)
        # Tabla de trivias
        cur.execute("""
            CREATE TABLE IF NOT EXISTS trivia (
                id SERIAL PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                hint TEXT NOT NULL
            )
        """)
init_db()

######################################
# FUNCIONES PARA CHISTES Y TRIVIAS
######################################
def get_random_joke():
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM jokes")
        joke_ids = [row[0] for row in cur.fetchall()]
    if not joke_ids:
        return "No hay chistes disponibles."
    joke_id = random.choice(joke_ids)
    with conn.cursor() as cur:
        cur.execute("SELECT joke_text FROM jokes WHERE id = %s", (joke_id,))
        joke = cur.fetchone()[0]
    return joke

def get_random_trivia():
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM trivia")
        trivia_list = cur.fetchall()
    if not trivia_list:
        return None
    return random.choice(trivia_list)

def normalize_string(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s)
                   if not unicodedata.combining(c)).replace(" ", "").lower()

active_trivia = {}  # key: channel.id, value: trivia_item

######################################
# CONFIGURACIÓN DEL BOT
######################################
bot = commands.Bot(command_prefix='?', intents=discord.Intents.default())

######################################
# COMANDOS DEL BOT
######################################
@bot.command()
async def chiste(ctx):
    await ctx.send(get_random_joke())

@bot.command()
async def trivia(ctx):
    trivia_item = get_random_trivia()
    if not trivia_item:
        await ctx.send("No hay trivias disponibles.")
        return
    active_trivia[ctx.channel.id] = trivia_item
    await ctx.send(f"**Trivia:** {trivia_item['question']}\n_Responde en el chat._")

######################################
# EVENTO ON_MESSAGE
######################################
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    # Tu código aquí
    await bot.process_commands(message)

    # Comprobar si hay una trivia activa en este canal
    if message.channel.id in active_trivia:
        trivia_item = active_trivia[message.channel.id]
        user_answer = normalize_string(message.content)
        correct_answer = normalize_string(trivia_item['answer'])
        if user_answer == correct_answer:
            await message.channel.send(f"¡Correcto, {message.author.mention}! 🎉")
            del active_trivia[message.channel.id]
        else:
            await message.channel.send(f"No es correcto. Pista: {trivia_item['hint']}")
        return

    await bot.process_commands(message)

######################################
# EVENTO ON_READY
######################################
@bot.event
async def on_ready():
    print(f'Bot de Entretenimiento conectado como {bot.user.name}')

######################################
# INICIAR EL BOT
######################################
bot.run(os.getenv('DISCORD_TOKEN'))

