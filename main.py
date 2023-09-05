import json

import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands
import datetime
import humanfriendly

logging = True
logsChannel = 1148384588800987287
file = open('config.json', 'r')
config = json.load(file)
bad_words = ["пидор", "пидорасы", "хохлы", "хохол", "пидоры", "негр",
             "негры", "нигретосы", "нигретос", "пидорас"]
adminRoles = ["Админ"]
intents = nextcord.Intents.default()
intents = nextcord.Intents().all()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"{bot.user.name} is ready!")


@bot.event
async def on_message(msg):
    if msg.author != bot.user:
        for text in bad_words:
            for i in adminRoles:
                if i not in str(msg.author.roles) and text in str(msg.content.lower()):
                    await msg.delete()
                    await msg.author.send("Не пишите плохие слова!!!")
                    if logging is True:
                        log_channel = bot.get_channel(logsChannel)
                        await log_channel.send(f"{msg.author.mention} написал плохие слова! Благо я удалил сообщение,"
                                               f" чтобы вы его не видели :3")


@bot.slash_command(description="Кикает пользователя с сервера.")
async def kick(interaction: nextcord.Interaction, user: nextcord.Member, reason: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Вы не являетесь администратором, "
                                                "потому вы не можете использовать эту команду!", ephemeral=True)
    else:
        await interaction.response.send_message(f"{user.mention} был кикнут!", ephemeral=True)
        if logging is True:
            log_channel = bot.get_channel(logsChannel)
            await log_channel.send(f"{user.mention} был кикнут админом {interaction.user.mention}. Причина: {reason}")
        await user.kick(reason=reason)


@bot.slash_command(description="Банит участника сервера.")
async def ban(interaction: nextcord.Interaction, user: nextcord.Member, reason: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Вы не являетесь администратором, "
                                                "потому вы не можете использовать эту команду!", ephemeral=True)
    else:
        await interaction.response.send_message(f"{user.mention} был забанен!", ephemeral=True)
        if logging is True:
            log_channel = bot.get_channel(logsChannel)
            await log_channel.send(f"{user.mention} был забанен админом {interaction.user.mention}. Причина: {reason}")
        await user.ban(reason=reason)


@bot.slash_command(description="Не даёт человеку писать на сервере некоторое время.")
async def mute(interaction: nextcord.Interaction, user: nextcord.Member, duration, reason: str):
    duration_sec = humanfriendly.parse_timespan(duration)
    await interaction.response.send_message(f"{user.mention} был замучен!", ephemeral=True)
    if logging is True:
        log_channel = bot.get_channel(logsChannel)
        await log_channel.send(f"{user.mention} был замучен админом {interaction.user.mention} на {duration}."
                               f" Причина: {reason}.")
    await user.edit(timeout=nextcord.utils.utcnow() + datetime.timedelta(seconds=duration_sec))


@bot.slash_command(description="Возвращает возможность писать в чат выбранному участнику сервера.")
async def unmute(interaction: nextcord.Interaction, user: nextcord.Member, reason: str):
    await interaction.response.send_message(f"{user.mention} был размучен!", ephemeral=True)
    if logging is True:
        log_channel = bot.get_channel(logsChannel)
        await log_channel.send(f"{user.mention} был размучен админом {interaction.user.mention}."
                               f" Причина: {reason}.")
    await user.edit(timeout=nextcord.utils.utcnow())


bot.run(config['token'])
