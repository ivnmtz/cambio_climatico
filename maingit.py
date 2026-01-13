import discord
from discord.ext import commands
import requests
from gtts import gTTS
import random
import os

# *CONFIGURACIÓN DEL BOT*
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# *VARIABLE GLOBAL*
ultimo_mensaje = ""

# *DICCIONARIO DE CONSEJOS ECOLÓGICOS SEGÚN EL CLIMA*
consejos_clima = {
    "soleado": [
        "Aprovecha el sol y no prendas focos ni luces en la casa",
        "Camina o usa bici porque el clima lo permite y no contaminas",
        "Evita usar el coche para trayectos cortos",
        "No uses aire acondicionado si no hace mucho calor",
        "Planta árboles o plantas porque crecen mejor con sol",
        "No quemes basura ni hojas porque el calor empeora la contaminación",
        "Usa energía solar si tienes algo pequeño como cargadores solares",
        "Mantén puertas y ventanas abiertas para no usar ventiladores",
        "Seca la ropa al sol para ahorrar energía",
        "Cuida parques y áreas verdes porque ayudan a limpiar el aire"
    ],

    "nublado": [
        "Usa transporte público porque no hace calor ni frío extremo",
        "Aprovecha para caminar sin cansarte tanto",
        "Apaga focos aunque el cielo esté oscuro",
        "Evita prender calefacción o aire acondicionado",
        "No quemes basura porque el humo se queda atrapado en el aire",
        "Revisa que tu casa no tenga fugas de gas",
        "Evita usar aerosoles porque contaminan más cuando el aire está quieto",
        "Limpia tu calle o banqueta para evitar contaminación",
        "Cuida árboles porque ayudan cuando el aire está pesado",
        "Habla con otros sobre cuidar el aire cuando está nublado"
    ],

    "lluvioso": [
        "No tires basura porque contamina el agua y el aire",
        "Evita usar el coche si no es necesario",
        "Apaga aparatos que no estés usando",
        "No quemes basura aunque esté mojada",
        "Mantén limpias las coladeras para evitar contaminación",
        "Aprovecha el agua de lluvia para no gastar más energía",
        "Usa paraguas en lugar de pedir un ride en coche",
        "Evita usar químicos fuertes que se van al ambiente",
        "Revisa que no haya fugas de gas por la humedad",
        "Recuerda que cuidar el aire también importa aunque esté lloviendo"
    ]
}

# *FUNCIÓN PARA OBTENER COORDENADAS*
def get_coordinates(city: str):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": city,
        "count": 1,
        "language": "es",
        "format": "json"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if "results" not in data:
            return None, None

        lat = data["results"][0]["latitude"]
        lon = data["results"][0]["longitude"]
        return lat, lon

    except Exception:
        return None, None

# *FUNCIÓN PARA OBTENER CLIMA Y TEMPERATURA*
def get_weather(city: str):
    lat, lon = get_coordinates(city)

    if lat is None or lon is None:
        return "desconocido", "N/A"

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        weather = data["current_weather"]
        temperatura = f'{weather["temperature"]}°C'
        code = weather["weathercode"]

        if code == 0:
            clima = "soleado"
        elif code in [1, 2, 3, 45, 48]:
            clima = "nublado"
        elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
            clima = "lluvioso"
        else:
            clima = "nublado"

        return clima, temperatura

    except Exception:
        return "desconocido", "N/A"

# *COMANDO CLIMA (TEXTO O VOICE CHAT)*
@bot.command()
async def clima(ctx, *, ciudad: str):
    global ultimo_mensaje

    usar_vc = False
    if ciudad.lower().endswith("vc"):
        usar_vc = True
        ciudad = ciudad[:-2].strip()

    clima_actual, temperatura = get_weather(ciudad)

    consejo = random.choice(
        consejos_clima.get(clima_actual, ["Mantén hábitos ecológicos todos los días"])
    )

    ultimo_mensaje = (
        f"Clima en {ciudad}: {clima_actual}. "
        f"Temperatura actual: {temperatura}. "
        f"Consejo ecológico: {consejo}"
    )

    if not usar_vc:
        await ctx.send(f"🌦️ **Clima en {ciudad}**: {clima_actual}")
        await ctx.send(f"🌡️ **Temperatura**: {temperatura}")
        await ctx.send(f"💡 **Consejo ecológico**: {consejo}")
        return

    if not ctx.author.voice:
        await ctx.send("❌ Debes estar en un canal de voz.")
        return

    canal = ctx.author.voice.channel

    if not ctx.voice_client:
        vc = await canal.connect()
    else:
        vc = ctx.voice_client

    tts = gTTS(text=ultimo_mensaje, lang="es")
    tts.save("clima_vc.mp3")

    if vc.is_playing():
        vc.stop()

    vc.play(discord.FFmpegPCMAudio("clima_vc.mp3"))

# *COMANDO DE SÍNTESIS DE VOZ*
@bot.command()
async def voz(ctx):
    global ultimo_mensaje

    if ultimo_mensaje == "":
        await ctx.send("❌ Primero usa el comando !clima.")
        return

    tts = gTTS(text=ultimo_mensaje, lang="es")
    tts.save("eco_consejo.mp3")

    await ctx.send("🔊 Escucha el reporte ecológico:")
    await ctx.send(file=discord.File("eco_consejo.mp3"))

    os.remove("eco_consejo.mp3")

# *COMANDO PARA SALIR DEL CANAL DE VOZ*
@bot.command()
async def salir(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Me salí del canal de voz.")


bot.run("aqui va tu token")