import datetime
import json
import sqlite3
import humanfriendly
import nextcord
from nextcord.ext import commands, tasks

# all necessary imported libraries are written above

logging = True
logsChannel = 1148384588800987287  # id of a log channel
file = open('config.json', 'r')  # you must create file with same name and make it must look like this inside:
# {
#   "token": "***your token***"
# }
config = json.load(file)  # this command loads config file with token
bad_words = ["пидор", "пидорасы", "хохлы", "хохол", "пидоры",
             "негр", "негры", "нигретосы", "нигретос", "нигеры", "нигер", "пидорас"]  # bad words list
adminRoles = ["Админ"]  # list of administrative roles
intents = nextcord.Intents().all()
bot = commands.Bot(command_prefix="!", intents=intents)  # creates usual command prefix, just because it is required for
# commands, that are not slash commands
conn = sqlite3.connect('users.db')  # creates a connection with database
cursor = conn.cursor()  # creates a cursor
cursor.execute("""CREATE TABLE IF  NOT EXISTS users (
    id INT,
    username TEXT,
    warns INT
)""")  # creates a table with name 'users' and columns 'id', 'username' and 'warns'
conn.commit()  # saves changes in database


# bot to startup


@bot.event
async def on_ready():  # this method shows, that the bot is running: it writes a message in terminal
    print(f"{bot.user.name} is ready!")
    await bot.change_presence(status=nextcord.Status.online, activity=nextcord.Activity(
        type=nextcord.ActivityType.watching, name="за сервером")) # this command changes bot status and activity

@bot.event
async def on_member_join(
        member):  # this method does a few things, when a user arrives: adds him a default role and also
    # send an embed message to a specific channel with greetings
    channel = bot.get_channel(909086509993459742)  # bot gets an ID of a specific "greetings" channel
    # (if you want to make this word, then change an ID to your own channel ID
    embed = nextcord.Embed(title="Добро пожаловать!!", description=f"{member.mention} зашел на сервер!")  # this creates
    # an embed message. You can change the title and the description of this message.
    await channel.send(embed=embed)  # this sends previously created embed message
    role = nextcord.utils.get(member.guild.roles, name='Подписчик')  # this command creates a function with
    # specific role, that you choose. You can change the name of the role, that you want to give, or you can delete
    # this command, if you don't need it.
    await member.add_roles(role)  # this command adds the role in the user role-list


@bot.event
async def on_message(msg):  # this is an AutoMod function, which is created to automaticaly moderate the chat.
    # This function doesn't linked to a specific channel, this moderates the WHOLE server.
    if msg.author != bot.user:  # checks, if user isn't a bot.
        for text in bad_words:  # bot chooses a word from a "bad word" list
            for i in adminRoles:  # bot chooses an administrative role from a list
                if i not in str(msg.author.roles) and text in str(msg.content.lower()):  # bot checks a word and
                    # comapares the word with words in "bad words" list in lower case
                    await msg.delete()  # deletes a message
                    if logging is True:  # checks, if he should save log in logging channel
                        log_channel = bot.get_channel(logsChannel)  # gets log channel id
                        # if user is not in 'users.db' database, then bot adds him there and add him a warning. If
                        # amount of warnings is more than 3, then bot bans him
                        cursor.execute(f"SELECT id FROM users WHERE id = {msg.author.id}")
                        result = cursor.fetchone()
                        if result is None:
                            cursor.execute(
                                f"INSERT INTO users VALUES ({msg.author.id}, '{msg.author.name}', 1)")  # adds
                            # user in database and gives him 1 warning
                            conn.commit()
                            await log_channel.send(f"{msg.author.mention} написал плохие слова! Благо я "
                                                   f"удалил сообщение,"
                                                   f" чтобы вы его не видели :3 \n Причина: Плохие слова.")
                        else:
                            cursor.execute(f"SELECT warns FROM users WHERE id = {msg.author.id}")
                            result = cursor.fetchone()
                            warns = result[0]
                            warns += 1
                            print(f"{msg.author.name} имеет {warns} предупреждений")
                            cursor.execute(f"UPDATE users SET warns = {warns} WHERE id = {msg.author.id}")
                            conn.commit()
                            if warns >= 3:
                                # send a message to a user, that he was banned
                                await msg.author.send("Вы были забанены за плохие слова!")
                                await log_channel.send(f"{msg.author.mention} написал плохие слова 3 раза! Благо я "
                                                       f"удалил сообщение "
                                                       f"и забанил его :3 \n Причина: Плохие слова.")
                                await msg.author.ban(reason="Плохие слова")
                                # delete all messages from user, that were written in the last 7 days
                                await msg.channel.purge(limit=100, check=lambda m: m.author == msg.author,
                                                        bulk=True)
                            else:
                                await msg.author.send("Не пишите плохие слова!!!")
                                await log_channel.send(f"{msg.author.mention} написал плохие слова! Благо я "
                                                       f"удалил сообщение,"
                                                       f" чтобы вы его не видели :3 \n Причина: Плохие слова.")


@bot.slash_command(description="Кикает пользователя с сервера.")  # this command is dedicated to kick user from server
async def kick(interaction: nextcord.Interaction, user: nextcord.Member, reason: str):  # this method requires to write
    # a nickname of user and a reason of kick
    if not interaction.user.guild_permissions.administrator:  # bot checks, if user,
        # that tries to use a command is an administrator
        await interaction.response.send_message("Вы не являетесь администратором, "
                                                "потому вы не можете использовать эту команду!", ephemeral=True)  #
        # this command sends a response, if user is not an administrator
    else:
        await interaction.response.send_message(f"{user.mention} был кикнут!", ephemeral=True)  # bot responds to
        # your command
        if logging is True:  # checks, if he should save log in logging channel
            log_channel = bot.get_channel(logsChannel)  # gets log channel id
            await log_channel.send(f"{user.mention} был кикнут админом {interaction.user.mention}."
                                   f" Причина: {reason}")  # sends message in the log channel
        await user.kick(reason=reason)  # bot bans a person


@bot.slash_command(description="Банит участника сервера.")  # this command is dedicated to ban user from server
async def ban(interaction: nextcord.Interaction, user: nextcord.Member, reason: str):
    if not interaction.user.guild_permissions.administrator:  # bot checks, if user,
        # that tries to use a command is an administrator
        await interaction.response.send_message("Вы не являетесь администратором, "
                                                "потому вы не можете использовать эту команду!", ephemeral=True)  #
        # this command sends a response, if user is not an administrator
    else:
        await interaction.response.send_message(f"{user.mention} был забанен!", ephemeral=True)  # bot responds to
        # your command
        # send a message to a user in private messages, that he was banned with a reason
        await user.send(f"Вы были забанены!\n Причина: {reason}")
        if logging is True:  # checks, if he should save log in logging channel
            log_channel = bot.get_channel(logsChannel)  # gets log channel id
            await log_channel.send(f"{user.mention} был забанен админом {interaction.user.mention}. "
                                   f"Причина: {reason}")  # sends message in the log channel
        await user.ban(reason=reason)  # bot bans a person


@bot.slash_command(description="Не даёт человеку писать на сервере некоторое время.")  # this command is dedicated
# to mute user on a server for a specific time
async def mute(interaction: nextcord.Interaction, user: nextcord.Member, duration, reason: str):  # this method requires
    # to write a nickname of user and a reason of kick
    if not interaction.user.guild_permissions.administrator:  # bot checks, if user,
        # that tries to use a command is an administrator
        await interaction.response.send_message("Вы не являетесь администратором, "
                                                "потому вы не можете использовать эту команду!", ephemeral=True)  #
        # this command sends a response, if user is not an administrator
    else:
        duration_sec = humanfriendly.parse_timespan(duration)  # turns usual time to a seconds
        # for example: "1m = 60 sec"
        await interaction.response.send_message(f"{user.mention} был замучен!", ephemeral=True)  # bot responds to
        # your command
        if logging is True:  # checks, if he should save log in logging channel
            log_channel = bot.get_channel(logsChannel)  # gets log channel id
            await log_channel.send(f"{user.mention} был замучен админом {interaction.user.mention} на {duration}."
                                   f" Причина: {reason}.")  # sends message in the log channel
        await user.edit(timeout=nextcord.utils.utcnow() + datetime.timedelta(seconds=duration_sec))  # bot mutes user
        # for a written time


@bot.slash_command(description="Возвращает возможность писать в чат выбранному участнику сервера.")  # this method is
# dedicated to unmute user and return him a possibility to write in chat and join a voice channels
async def unmute(interaction: nextcord.Interaction, user: nextcord.Member, reason: str):  # this method requires
    # to write a nickname of user and a reason of unmute
    if not interaction.user.guild_permissions.administrator:  # bot checks, if user,
        # that tries to use a command is an administrator
        await interaction.response.send_message("Вы не являетесь администратором, "
                                                "потому вы не можете использовать эту команду!", ephemeral=True)  #
        # this command sends a response, if user is not an administrator
    else:
        await interaction.response.send_message(f"{user.mention} был размучен!", ephemeral=True)  # bot responds to
        # your command
        if logging is True:  # checks, if he should save log in logging channel
            log_channel = bot.get_channel(logsChannel)  # gets log channel id
            await log_channel.send(f"{user.mention} был размучен админом {interaction.user.mention}."
                                   f" Причина: {reason}.")  # sends message in the log channel
        await user.edit(timeout=nextcord.utils.utcnow())  # this command changes the mute time to the current UTC time,
    # which removes the mute


@bot.slash_command(description="Удаляет определенное сообщение по id и выбранному каналу.")
async def delete_message(interaction: nextcord.Interaction, channel: nextcord.TextChannel, message_id, reason: str):
    message_id = int(message_id)
    msg = await channel.fetch_message(message_id)
    if not interaction.user.guild_permissions.administrator:  # bot checks, if user,
        # that tries to use a command is an administrator
        await interaction.response.send_message("Вы не являетесь администратором, "
                                                "потому вы не можете использовать эту команду!", ephemeral=True)  #
        # this command sends a response, if user is not an administrator
    else:
        await interaction.response.send_message(f"Сообщение пользователя {msg.author.mention} было удалено!",
                                                ephemeral=True)
        if logging is True:  # checks, if he should save log in logging channel
            log_channel = bot.get_channel(logsChannel)  # gets log channel id
            await log_channel.send(f"{msg.author.mention} написал плохие слова! Благо {interaction.user.mention} "
                                   f"удалил сообщение,"
                                   f" чтобы вы его не видели :3 \n Причина: {reason}.")

            await msg.delete()


@bot.slash_command(description="Показывает список предупреждений пользователя.")
async def warns(interaction: nextcord.Interaction, user: nextcord.Member):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Вы не являетесь администратором, "
                                                "потому вы не можете использовать эту команду!", ephemeral=True)
    else:
        cursor.execute(f"SELECT warns FROM users WHERE id = {user.id}")
        result = cursor.fetchone()
        warns = result[0]
        await interaction.response.send_message(f"У пользователя {user.mention} {warns} предупреждений.",
                                                ephemeral=True)


@bot.slash_command(description="Разбанивает пользователя по id.")
async def unban(interaction: nextcord.Interaction, user_id, reason: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Вы не являетесь администратором, "
                                                "потому вы не можете использовать эту команду!", ephemeral=True)
    else:
        await interaction.response.send_message(f"Пользователь с id {user_id} был разбанен!", ephemeral=True)
        if logging is True:
            log_channel = bot.get_channel(logsChannel)
            await log_channel.send(f"<@{user_id}> был разбанен админом {interaction.user.mention}. "
                                   f"Причина: {reason}")
        cursor.execute(f"DELETE FROM users WHERE id = {user_id}")
        await interaction.guild.unban(nextcord.Object(user_id), reason=reason)
        conn.commit()

bot.run(config['token'])  # bot runs up and gets a token from config file
