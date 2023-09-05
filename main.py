import json

import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

file = open('config.json', 'r')
config = json.load(file)
bad_words = ["пидор", "пидорасы", "хохлы", "хохол", "пидоры", "негр",
             "негры", "нигретосы", "нигретос", "пидорас"]
adminRoles = ["Админ", "Модератор"]
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


logging = True
logsChannel = 1148384588800987287


@bot.slash_command()
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


bot.run(config['token'])
