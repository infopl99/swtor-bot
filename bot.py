import os
import requests
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

import sqlite3

# Connexion à la base de données (création si elle n'existe pas)
conn = sqlite3.connect("swtor_bot.db")
cursor = conn.cursor()

# Création d'une table pour stocker les builds
cursor.execute("""
CREATE TABLE IF NOT EXISTS builds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    classe TEXT NOT NULL,
    spécialisation TEXT NOT NULL,
    description TEXT NOT NULL
)
""")

conn.commit()
conn.close()

print("Base de données SQLite prête !")

@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user}")

@bot.command()  
async def hello(ctx):  
    await ctx.send("Salut, je suis ton assistant SWTOR !")

@bot.command()
async def question(ctx, *, message: str = None):
    """Pose une question et Llama 3 répond !"""
    if message is None:
        await ctx.send("❌ Tu dois poser une question ! Ex: `!question Comment bien débuter dans SWTOR ?`")
        return
    
    try:
        url = "https://api.together.xyz/v1/completions"
        headers = {"Authorization": f"Bearer {TOGETHER_API_KEY}", "Content-Type": "application/json"}
        data = {
            "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            "prompt": message,
            "max_tokens": 200
        }

        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        
        # Vérifier si la requête API a bien fonctionné
        if "choices" in result:
            answer = result["choices"][0]["text"]
            await ctx.send(answer)
        else:
            await ctx.send("❌ Erreur dans la réponse de l'API :")
            await ctx.send(f"```{result}```")  # Affiche la réponse brute de l'API pour debug

    except Exception as e:
        await ctx.send("❌ Une erreur est survenue, regarde la console.")
        print(f"Erreur API : {e}")  # Affiche l'erreur exacte dans la console

@bot.command()
async def ajouter_build(ctx, classe: str, spécialisation: str, *, description: str):
    """Ajoute un build à la base de données"""
    conn = sqlite3.connect("swtor_bot.db")
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO builds (classe, spécialisation, description) VALUES (?, ?, ?)",
                   (classe, spécialisation, description))
    
    conn.commit()
    conn.close()
    
    await ctx.send(f"✅ Build ajouté : {classe} - {spécialisation} !")

@bot.command()
async def voir_build(ctx, classe: str, spécialisation: str):
    """Affiche un build enregistré"""
    conn = sqlite3.connect("swtor_bot.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT description FROM builds WHERE classe = ? AND spécialisation = ?", 
                   (classe, spécialisation))
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        await ctx.send(f"📜 Build {classe} - {spécialisation} : {result[0]}")
    else:
        await ctx.send("❌ Aucun build trouvé pour cette classe/spécialisation.")

@bot.command()
async def modifier_build(ctx, classe: str, spécialisation: str, *, nouvelle_description: str):
    """Modifie la description d'un build"""
    conn = sqlite3.connect("swtor_bot.db")
    cursor = conn.cursor()
    
    cursor.execute("UPDATE builds SET description = ? WHERE classe = ? AND spécialisation = ?", 
                   (nouvelle_description, classe, spécialisation))
    
    if cursor.rowcount == 0:
        await ctx.send("❌ Aucun build trouvé pour cette classe/spécialisation.")
    else:
        conn.commit()
        await ctx.send(f"✅ Build {classe} - {spécialisation} mis à jour !")

    conn.close()

@bot.command()
async def supprimer_build(ctx, classe: str, spécialisation: str):
    """Supprime un build de la base de données"""
    conn = sqlite3.connect("swtor_bot.db")
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM builds WHERE classe = ? AND spécialisation = ?", (classe, spécialisation))
    
    if cursor.rowcount == 0:
        await ctx.send("❌ Aucun build trouvé pour cette classe/spécialisation.")
    else:
        conn.commit()
        await ctx.send(f"🗑️ Build {classe} - {spécialisation} supprimé !")

    conn.close()

bot.run(TOKEN)
