import datetime
import json
import sqlite3
import random
import humanfriendly
import nextcord
from nextcord.ext import commands

# all necessary imported libraries are written in requirements.txt

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
# create database, where the bot will store user id, username, lvl, and total amount of messages, that he wrote. Lvl
# will be calculated by the amount of messages, that user wrote. For example: 10 messages = 1 lvl, 20 messages = 2 lvl
# etc.
new_lvl_channel = 1168564388194689116
lvl_db = sqlite3.connect('lvl.db')  # creates a connection with database
lvl_cursor = lvl_db.cursor()  # creates a cursor
lvl_cursor.execute("""CREATE TABLE IF  NOT EXISTS users (
    id INT,
    username TEXT,
    lvl INT,
    messages INT
)""")
# create a list of channels, where user won't be able to increase his amount of messages and lvl
exclude_channels = [909083335064682519, 1042869059378749460, 1168564388194689116, 1057611114126524446,
                    1078383537171996723,
                    909094954129850418, 909198474061443153, 1155510065508401203, 1057604521888579604,
                    1057454748611137559,
                    909203930725093416, 909204194697809951, 1042868984950820934, 1156421256896319598,
                    909086509993459742]


# bot to startup


@bot.event
async def on_ready():  # this method shows, that the bot is running: it writes a message in terminal
    print(f"{bot.user.name} is ready!")
    await bot.change_presence(status=nextcord.Status.online, activity=nextcord.Activity(
        type=nextcord.ActivityType.watching, name="за сервером"))  # this command changes bot status and activity


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
                            break
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
                                break
                            else:
                                await msg.author.send("Не пишите плохие слова!!!")
                                await log_channel.send(f"{msg.author.mention} написал плохие слова! Благо я "
                                                       f"удалил сообщение,"
                                                       f" чтобы вы его не видели :3 \n Причина: Плохие слова.")
                                break
        # check if channel, where user wrote a message, is in exclude_channels list
        if msg.channel.id not in exclude_channels:
            # check if a message is a slash-command
            if msg.content.startswith("/") is False:
                lvl_cursor.execute(f"SELECT id FROM users WHERE id = {msg.author.id}")
                result = lvl_cursor.fetchone()
                if result is None:
                    lvl_cursor.execute(
                        f"INSERT INTO users VALUES ({msg.author.id}, '{msg.author.name}', 0, 1)")
                    lvl_db.commit()
                else:
                    lvl_cursor.execute(f"SELECT messages FROM users WHERE id = {msg.author.id}")
                    result = lvl_cursor.fetchone()
                    messages = result[0]
                    messages += 1
                    print(f"{msg.author.name} написал {messages} сообщений")
                    lvl_cursor.execute(f"UPDATE users SET messages = {messages} WHERE id = {msg.author.id}")
                    lvl_db.commit()
                    lvl_cursor.execute(f"SELECT lvl FROM users WHERE id = {msg.author.id}")
                    result = lvl_cursor.fetchone()
                    lvl = result[0]
                    if messages >= 10 * (lvl + 1):
                        lvl += 1
                        lvl_logging_channel = bot.get_channel(new_lvl_channel)
                        embed = nextcord.Embed(title="Поздравляем!", description=f"{msg.author.mention} "
                                                                                 f"получил {lvl} уровень!")
                        await lvl_logging_channel.send(embed=embed)
                        lvl_cursor.execute(f"UPDATE users SET lvl = {lvl} WHERE id = {msg.author.id}")
                        lvl_db.commit()
                        await msg.channel.send(f"Поздравляем, {msg.author.mention}! Вы получили {lvl} уровень!")
                        lvl_cursor.execute(f"UPDATE users SET messages = 0 WHERE id = {msg.author.id}")
                        lvl_db.commit()
        else:
            pass


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
        if warns is None:
            await interaction.response.send_message(f"У пользователя {user.mention} нет предупреждений.",
                                                    ephemeral=True)
        elif warns == 1:
            await interaction.response.send_message(f"У пользователя {user.mention} 1 предупреждение.",
                                                    ephemeral=True)
        elif warns == 2 or warns == 3 or warns == 4:
            await interaction.response.send_message(f"У пользователя {user.mention} {warns} предупреждения.",
                                                    ephemeral=True)
        else:
            await interaction.response.send_message(f"У пользователя {user.mention} {warns} предупреждений.",
                                                    ephemeral=True)


# write a command, that gives user a warning
@bot.slash_command(description="Выдаёт предупреждение пользователю.")
async def warn(interaction: nextcord.Interaction, user: nextcord.Member, reason: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Вы не являетесь администратором, "
                                                "потому вы не можете использовать эту команду!", ephemeral=True)
    else:
        await interaction.response.send_message(f"Пользователь {user.mention} получил предупреждение!",
                                                ephemeral=True)
        if logging is True:  # checks, if he should save log in logging channel
            log_channel = bot.get_channel(logsChannel)  # gets log channel id
            await log_channel.send(f"{user.mention} получил предупреждение от {interaction.user.mention}."
                                   f" Причина: {reason}.")  # sends message in the log channel
        cursor.execute(f"SELECT id FROM users WHERE id = {user.id}")
        result = cursor.fetchone()
        if result is None:
            cursor.execute(
                f"INSERT INTO users VALUES ({user.id}, '{user.name}', 1)")  # adds
            # user in database and gives him 1 warning
            conn.commit()
        else:
            cursor.execute(f"SELECT warns FROM users WHERE id = {user.id}")
            result = cursor.fetchone()
            warns = result[0]
            warns += 1
            print(f"{user.name} имеет {warns} предупреждений")
            cursor.execute(f"UPDATE users SET warns = {warns} WHERE id = {user.id}")
            conn.commit()


# write a command, that removes all warns from user
@bot.slash_command(description="Удаляет все предупреждения пользователя.")
async def clear_warns(interaction: nextcord.Interaction, user: nextcord.Member, reason: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Вы не являетесь администратором, "
                                                "потому вы не можете использовать эту команду!", ephemeral=True)
    else:
        await interaction.response.send_message(f"Все предупреждения пользователя {user.mention} были удалены!",
                                                ephemeral=True)
        if logging is True:  # checks, if he should save log in logging channel
            log_channel = bot.get_channel(logsChannel)  # gets log channel id
            await log_channel.send(
                f"Все предупреждения пользователя {user.mention} были удалены админом {interaction.user.mention}."
                f" Причина: {reason}.")  # sends message in the log channel
        cursor.execute(f"UPDATE users SET warns = 0 WHERE id = {user.id}")
        conn.commit()


# write a command, that clears all warns on a server
@bot.slash_command(description="Удаляет все предупреждения на сервере.")
async def clear_all_warns(interaction: nextcord.Interaction, reason: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Вы не являетесь администратором, "
                                                "потому вы не можете использовать эту команду!", ephemeral=True)
    else:
        await interaction.response.send_message(f"Все предупреждения на сервере были удалены!",
                                                ephemeral=True)
        if logging is True:
            log_channel = bot.get_channel(logsChannel)
            await log_channel.send(f"Все предупреждения на сервере были удалены админом {interaction.user.mention}."
                                   f" Причина: {reason}.")
        cursor.execute(f"UPDATE users SET warns = 0")
        conn.commit()


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


# write a slash-command with a rock-paper-scissors game with random bot choice
@bot.slash_command(description="Играет с вами в камень-ножницы-бумага.")
async def rps(interaction: nextcord.Interaction, choice):
    choices = ["камень", "бумага", "ножницы"]
    bot_choice = random.choice(choices)
    if choice == "камень":
        if bot_choice == "камень":
            await interaction.response.send_message("Ничья!", ephemeral=True)
        elif bot_choice == "бумага":
            await interaction.response.send_message("Я выиграл!", ephemeral=True)
        elif bot_choice == "ножницы":
            await interaction.response.send_message("Вы выиграли!", ephemeral=True)
    elif choice == "бумага":
        if bot_choice == "камень":
            await interaction.response.send_message("Вы выиграли!", ephemeral=True)
        elif bot_choice == "бумага":
            await interaction.response.send_message("Ничья!", ephemeral=True)
        elif bot_choice == "ножницы":
            await interaction.response.send_message("Я выиграл!", ephemeral=True)
    elif choice == "ножницы":
        if bot_choice == "камень":
            await interaction.response.send_message("Я выиграл!", ephemeral=True)
        elif bot_choice == "бумага":
            await interaction.response.send_message("Вы выиграли!", ephemeral=True)
        elif bot_choice == "ножницы":
            await interaction.response.send_message("Ничья!", ephemeral=True)
    else:
        await interaction.response.send_message("Вы должны выбрать из этих вариантов: камень, бумага, ножницы",
                                                ephemeral=True)


# write a slash-command, that sends full list of slash-commands in alphabetical order as an embed message
@bot.slash_command(description="Показывает список всех команд.")
async def commands(interaction: nextcord.Interaction):
    embed = nextcord.Embed(title="Список всех команд", description="Все команды, которые есть на этом сервере.",
                           color=0x00ff00)
    embed.add_field(name="!ban", value="Банит участника сервера.", inline=False)
    embed.add_field(name="!clear_all_warns", value="Удаляет все предупреждения на сервере.", inline=False)
    embed.add_field(name="!clear_warns", value="Удаляет все предупреждения пользователя.", inline=False)
    embed.add_field(name="!coinflip", value="Играет с вами в подбрасывание монетки.", inline=False)
    embed.add_field(name="!delete_message", value="Удаляет определенное сообщение по id и выбранному каналу.",
                    inline=False)
    embed.add_field(name="!kick", value="Кикает пользователя с сервера.", inline=False)
    embed.add_field(name="!mute", value="Не даёт человеку писать на сервере некоторое время.", inline=False)
    embed.add_field(name="!profile", value="Показывает ваш уровень и количество сообщений, которые вы написали.",
                    inline=False)
    embed.add_field(name="!rps", value="Играет с вами в камень-ножницы-бумага.", inline=False)
    embed.add_field(name="!unban", value="Разбанивает пользователя по id.", inline=False)
    embed.add_field(name="!unmute", value="Возвращает возможность писать в чат выбранному участнику сервера.",
                    inline=False)
    embed.add_field(name="!warn", value="Выдаёт предупреждение пользователю.", inline=False)
    embed.add_field(name="!warns", value="Показывает список предупреждений пользователя.", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.slash_command(description="Показывает ваш уровень и количество сообщений, которые вы написали.")
async def profile(interaction: nextcord.Interaction):
    lvl_cursor.execute(f"SELECT id FROM users WHERE id = {interaction.user.id}")
    result = lvl_cursor.fetchone()
    if result is None:
        lvl_cursor.execute(
            f"INSERT INTO users VALUES ({interaction.user.id}, '{interaction.user.name}', 0, 0)")
        lvl_db.commit()
        await interaction.response.send_message("Вы ещё не написали ни одного сообщения!", ephemeral=True)
    else:
        lvl_cursor.execute(f"SELECT lvl FROM users WHERE id = {interaction.user.id}")
        result = lvl_cursor.fetchone()
        lvl = result[0]
        lvl_cursor.execute(f"SELECT messages FROM users WHERE id = {interaction.user.id}")
        result = lvl_cursor.fetchone()
        messages = result[0]
        embed = nextcord.Embed(title=f"Профиль {interaction.user.name}", description=f"Уровень: {lvl}\n"
                                                                                     f"Сообщений: {(10*lvl) + messages}",
                               color=0x00ff00)
        embed.set_thumbnail(url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.slash_command(description="Играет с вами в подбрасывание монетки.")
async def coinflip(interaction: nextcord.Interaction):
    choices = ["орёл", "решка"]
    bot_choice = random.choice(choices)
    await interaction.response.send_message(f"Выпало: {bot_choice}", ephemeral=True)


bot.run(config['token'])  # bot runs up and gets a token from config file
