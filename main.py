import datetime
import json
import sqlite3
import random
import datetime
import aiohttp
from PIL import Image
from io import BytesIO
from colorthief import ColorThief
from twitch_notifications import checkIfLive

import humanfriendly
import nextcord
from nextcord.ext import commands, tasks

# all necessary imported libraries are written in requirements.txt

logging = True
logsChannel = 1148384588800987287  # id of a log channel
notif_channel = 1042869059378749460
file = open('config.json', 'r')  # you must create file with same name and make it must look like this inside:
# {
#   "token": "***your token***"
# }
config = json.load(file)  # this command loads config file with token
adminRoles = ["Админ", "Основатель", "Бездушные машины"]  # list of administrative roles
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
new_lvl_channel = 1168564388194689116
lvl_db = sqlite3.connect('lvl.db')  # creates a connection with database
lvl_cursor = lvl_db.cursor()  # creates a cursor
lvl_cursor.execute("""CREATE TABLE IF  NOT EXISTS users (
    id INT,
    username TEXT,
    lvl INT,
    messages INT
)""")
avatar = open("avatar.gif", "rb")
bad_words_db = sqlite3.connect('bad_words.db')
bad_words_cursor = bad_words_db.cursor()
bad_words_cursor.execute("""CREATE TABLE IF NOT EXISTS bad_words (
    id INT,
    word TEXT
)""")
# create a list of channels, where user won't be able to increase his amount of messages and lvl
exclude_channels = [909083335064682519, 1042869059378749460, 1168564388194689116, 1057611114126524446,
                    1078383537171996723,
                    909094954129850418, 909198474061443153, 1155510065508401203, 1057604521888579604,
                    1057454748611137559,
                    909203930725093416, 909204194697809951, 1042868984950820934, 1156421256896319598,
                    909086509993459742, 909089711501504532, 1258808539326058537]
exclude_categories = [1052532014844235816]
lvl_roles = {
    "УРОВЕНЬ 60 - ЛЕГЕНДА": 60,
    "УРОВЕНЬ 30 - БЫВАЛЫЙ ПОДПИСЧИК": 30,
    "УРОВЕНЬ 10 - АКТИВНЫЙ ПОДПИСЧИК": 10,
    "УРОВЕНЬ 1 - МОЛОКОСОС": 1
}
streamers_db = sqlite3.connect("streamers.db")
streamers_cursor = streamers_db.cursor()
# command creates a database with nickname of streamers and also store their status there
streamers_cursor.execute("""CREATE TABLE IF NOT EXISTS streamers (
    nickname TEXT,
    status TEXT
)""")


# bot to startup


@bot.event
async def on_ready():  # this method shows, that the bot is running: it writes a message in terminal
    print(f"{bot.user.name} is ready!")
    twitchNotifications.start()
    await bot.change_presence(status=nextcord.Status.online, activity=nextcord.Activity(
        type=nextcord.ActivityType.watching, name="за сервером")) and bot.user.edit(
        avatar=avatar.read()) and check_lvl_roles()  # this command
    # changes bot status and activity


@bot.event
async def on_member_join(member):
    channel = bot.get_channel(909086509993459742)
    embed = nextcord.Embed(title="Добро пожаловать!!", description=f"{member.mention} зашел на сервер!",
                           color=nextcord.Color.blue())
    await channel.send(embed=embed)
    role = nextcord.utils.get(member.guild.roles, name='Подписчик')
    await member.add_roles(role)


async def update_member_roles(member, lvl):
    for role_name, required_lvl in lvl_roles.items():
        role = nextcord.utils.get(member.guild.roles, name=role_name)
        if role is not None:
            if lvl >= required_lvl and role not in member.roles:
                await member.add_roles(role)
            elif lvl < required_lvl and role in member.roles:
                await member.remove_roles(role)


@bot.event
async def check_lvl_roles():
    while True:
        for guild in bot.guilds:
            for member in guild.members:
                if not member.bot:
                    lvl_cursor.execute("SELECT lvl FROM users WHERE id = ?", (member.id,))
                    result = lvl_cursor.fetchone()
                    if result is not None:
                        lvl = result[0]
                        await update_member_roles(member, lvl)
                else:
                    for role_name in lvl_roles:
                        role = nextcord.utils.get(guild.roles, name=role_name)
                        if role in member.roles:
                            await member.remove_roles(role)
        await nextcord.utils.sleep_until(datetime.datetime.now() + datetime.timedelta(minutes=1))


@bot.event
async def on_message(msg):
    if msg.author == bot.user:
        return

    # Retrieve bad words list once, instead of on every message
    bad_words_cursor.execute("SELECT word FROM bad_words")
    bad_words_list = set(word[0] for word in bad_words_cursor.fetchall())
    author_roles = {role.id for role in msg.author.roles}

    if not author_roles.intersection(adminRoles):
        if any(word in msg.content.lower().split() for word in bad_words_list):
            await msg.delete()
            if logging:
                log_channel = bot.get_channel(logsChannel)
                cursor.execute("SELECT warns FROM users WHERE id = ?", (msg.author.id,))
                result = cursor.fetchone()
                if result is None:
                    cursor.execute("INSERT INTO users (id, name, warns) VALUES (?, ?, 1)",
                                   (msg.author.id, msg.author.name))
                    conn.commit()
                    await log_channel.send(
                        f"{msg.author.mention} написал плохие слова! Сообщение удалено. Причина: Плохие слова.")
                else:
                    warns = result[0] + 1
                    cursor.execute("UPDATE users SET warns = ? WHERE id = ?", (warns, msg.author.id))
                    conn.commit()
                    if warns >= 3:
                        await msg.author.send("Вы были забанены за плохие слова!")
                        await log_channel.send(
                            f"{msg.author.mention} написал плохие слова 3 раза! Сообщение удалено и пользователь"
                            f" забанен. Причина: Плохие слова.")
                        await msg.author.ban(reason="Плохие слова")
                        await msg.channel.purge(limit=100, check=lambda m: m.author == msg.author, bulk=True)
                        lvl_cursor.execute("DELETE FROM users WHERE id = ?", (msg.author.id,))
                    else:
                        await msg.author.send("Не пишите плохие слова!!!")
                        await log_channel.send(
                            f"{msg.author.mention} написал плохие слова! Сообщение удалено. Причина: Плохие слова.")

    if (msg.channel.category and msg.channel.category.id not in exclude_categories and
            msg.channel.id not in exclude_channels and
            not msg.content.startswith("/")):
        lvl_cursor.execute("SELECT messages, lvl FROM users WHERE id = ?", (msg.author.id,))
        result = lvl_cursor.fetchone()
        if result is None:
            lvl_cursor.execute("INSERT INTO users (id, name, messages, lvl) VALUES (?, ?, 1, 0)",
                               (msg.author.id, msg.author.name))
            lvl_db.commit()
            await check_lvl_roles()
        else:
            messages, lvl = result
            messages += 1
            lvl_cursor.execute("UPDATE users SET messages = ? WHERE id = ?", (messages, msg.author.id))
            lvl_db.commit()
            if messages >= 10 * (lvl + 1):
                lvl += 1
                lvl_cursor.execute("UPDATE users SET lvl = ?, messages = 0 WHERE id = ?", (lvl, msg.author.id))
                lvl_db.commit()
                lvl_logging_channel = bot.get_channel(new_lvl_channel)
                embed = nextcord.Embed(title="Поздравляем!", description=f"{msg.author.mention} получил {lvl} уровень!")
                await lvl_logging_channel.send(embed=embed)
                await update_member_roles(msg.author, lvl)


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


@bot.slash_command(description="Показывает количество сообщений в канале")
async def messages_count(interaction: nextcord.Interaction):
    messages = interaction.channel.history()
    count = 0
    async for message in messages:
        count += 1
    await interaction.response.send_message(f"Количество сообщений в канале: {count}", ephemeral=True)


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
async def mute(interaction: nextcord.Interaction, user: nextcord.Member, duration: str, reason: str):
    # Check if the user invoking the command has administrator permissions
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Вы не являетесь администратором, поэтому не можете использовать эту команду!", ephemeral=True)
        return

    # Attempt to convert the provided duration to seconds
    try:
        duration_sec = humanfriendly.parse_timespan(duration)
    except ValueError:
        # Inform the user if the provided duration format is incorrect
        await interaction.response.send_message("Некорректный формат времени. Используйте, например, '10s' для 10 секунд, '5m' для 5 минут, и т.д.", ephemeral=True)
        return

    # Apply the mute by setting the user's timeout until the specified end time
    mute_end_time = nextcord.utils.utcnow() + datetime.timedelta(seconds=duration_sec)
    await user.edit(timeout=mute_end_time)  # Set the time until which the user will be muted

    # Log the mute action if logging is enabled
    if logging:
        log_channel = bot.get_channel(logsChannel)
        await log_channel.send(
            f"{user.mention} был замучен администратором {interaction.user.mention} на {duration}. Причина: {reason}.")

    # Send a message indicating that the user has been muted
    await interaction.response.send_message(f"{user.mention} был замучен на {duration}!", ephemeral=True)


@bot.slash_command(description="Возвращает возможность писать в чат выбранному участнику сервера.")  # this method is
# dedicated to unmute user and return him a possibility to write in chat and join a voice channels
async def unmute(interaction: nextcord.Interaction, user: nextcord.Member, reason: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Вы не являетесь администратором, поэтому не можете использовать эту команду!", ephemeral=True)
        return

    await user.edit(timeout=None)
    await interaction.response.send_message(f"{user.mention} был размучен!", ephemeral=True)

    if logging:
        log_channel = bot.get_channel(logsChannel)
        await log_channel.send(f"{user.mention} был размучен администратором {interaction.user.mention}. Причина: {reason}.")


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
    # Проверяем, является ли пользователь администратором или запрашивает информацию о себе
    if not interaction.user.guild_permissions.administrator and interaction.user != user:
        await interaction.response.send_message(
            "Вы не являетесь администратором и не можете просматривать предупреждения других пользователей.",
            ephemeral=True
        )
        return

    # Получаем количество предупреждений пользователя
    cursor.execute("SELECT warns FROM users WHERE id = ?", (user.id,))
    result = cursor.fetchone()
    warns_count = result[0] if result else 0

    # Определяем сообщение в зависимости от того, кто просматривает предупреждения
    if interaction.user == user:
        if warns_count == 0:
            message = "У вас нет предупреждений."
        elif warns_count == 1:
            message = "У вас 1 предупреждение."
        elif 2 <= warns_count <= 4:
            message = f"У вас {warns_count} предупреждения."
        else:
            message = f"У вас {warns_count} предупреждений."
    else:
        if warns_count == 0:
            message = f"У пользователя {user.mention} нет предупреждений."
        elif warns_count == 1:
            message = f"У пользователя {user.mention} 1 предупреждение."
        elif 2 <= warns_count <= 4:
            message = f"У пользователя {user.mention} {warns_count} предупреждения."
        else:
            message = f"У пользователя {user.mention} {warns_count} предупреждений."

    await interaction.response.send_message(message, ephemeral=True)


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
            warns_count = result[0]
            warns_count += 1
            print(f"{user.name} имеет {warns_count} предупреждений")
            cursor.execute(f"UPDATE users SET warns = {warns_count} WHERE id = {user.id}")
            conn.commit()


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


@bot.slash_command(description="Играет с вами в камень-ножницы-бумага.")
async def rps(interaction: nextcord.Interaction, choice: str):
    choices = ["камень", "бумага", "ножницы"]
    choice = choice.lower()

    if choice not in choices:
        await interaction.response.send_message("Вы должны выбрать из этих вариантов: камень, бумага, ножницы",
                                                ephemeral=True)
        return

    bot_choice = random.choice(choices)
    result_messages = {
        ("камень", "камень"): "Ничья!",
        ("камень", "бумага"): "Я выиграл!",
        ("камень", "ножницы"): "Вы выиграли!",
        ("бумага", "камень"): "Вы выиграли!",
        ("бумага", "бумага"): "Ничья!",
        ("бумага", "ножницы"): "Я выиграл!",
        ("ножницы", "камень"): "Я выиграл!",
        ("ножницы", "бумага"): "Вы выиграли!",
        ("ножницы", "ножницы"): "Ничья!",
    }

    result = result_messages[(choice, bot_choice)]
    await interaction.response.send_message(result, ephemeral=True)


@bot.slash_command(description="Добавляет плохое слово(плохие слова) в базу данных.")
async def add_bad_word(interaction: nextcord.Interaction, word: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Вы не являетесь администратором, "
                                                "потому вы не можете использовать эту команду!", ephemeral=True)
    else:
        if "," in word:
            words = word.split(", ")
            for i in words:
                bad_words_cursor.execute(f"INSERT INTO bad_words VALUES ({random.randint(1, 100000)}, '{i}')")
                bad_words_db.commit()
            await interaction.response.send_message(f"Слова {words} были добавлены в базу данных!", ephemeral=True)
        else:
            bad_words_cursor.execute(f"INSERT INTO bad_words VALUES ({random.randint(1, 100000)}, '{word}')")
            bad_words_db.commit()
            await interaction.response.send_message(f"Слово {word} было добавлено в базу данных!", ephemeral=True)


@bot.slash_command(description="Удаляет плохое слово из базы данных.")
async def remove_bad_word(interaction: nextcord.Interaction, word: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Вы не являетесь администратором, "
                                                "потому вы не можете использовать эту команду!", ephemeral=True)
    else:
        bad_words_cursor.execute(f"DELETE FROM bad_words WHERE word = '{word}'")
        bad_words_db.commit()
        await interaction.response.send_message(f"Слово {word} было удалено из базы данных!", ephemeral=True)


@bot.slash_command(description="Показывает список всех плохих слов.")
async def bad_words(interaction: nextcord.Interaction):
    bad_words_cursor.execute("SELECT word FROM bad_words")
    bad_words = bad_words_cursor.fetchall()
    embed = nextcord.Embed(title="Список плохих слов", description="Список всех плохих слов в базе данных.",
                           color=0x223eff)
    for i in bad_words:
        embed.add_field(name="Слово", value=i[0], inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.slash_command(description="Показывает список всех команд в алфавитном порядке.")
async def commands(interaction: nextcord.Interaction):
    commands_dict = {
        "/add_bad_word": "Добавляет плохое слово(плохие слова) в базу данных.",
        "/add_streamer": "Добавляет стримера в базу данных.",
        "/bad_words": "Показывает список всех плохих слов.",
        "/ban": "Банит участника сервера.",
        "/clear_all_warns": "Удаляет все предупреждения на сервере.",
        "/clear_warns": "Удаляет все предупреждения пользователя.",
        "/coinflip": "Играет с вами в подбрасывание монетки.",
        "/delete_message": "Удаляет определенное сообщение по id и выбранному каналу.",
        "/kick": "Кикает пользователя с сервера.",
        "/leaderboard": "Показывает таблицу лидеров по уровню и количеству сообщений с их количеством сообщений.",
        "/messages_count": "Показывает количество сообщений в канале.",
        "/mute": "Не даёт человеку писать на сервере некоторое время.",
        "/profile": "Показывает ваш уровень и количество сообщений, которые вы написали.",
        "/remove_bad_word": "Удаляет плохое слово из базы данных.",
        "/remove_streamer": "Удаляет стримера из базы данных.",
        "/rps": "Играет с вами в камень-ножницы-бумага.",
        "/unban": "Разбанивает пользователя по id.",
        "/unmute": "Возвращает возможность писать в чат выбранному участнику сервера.",
        "/warn": "Выдаёт предупреждение пользователю.",
        "/warns": "Показывает список предупреждений пользователя."
    }

    sorted_commands = dict(sorted(commands_dict.items()))

    embed_commands = nextcord.Embed(
        title="Список всех команд",
        description="Список всех команд в алфавитном порядке.",
        color=0x223eff
    )

    for command, description in sorted_commands.items():
        embed_commands.add_field(name=command, value=description, inline=False)

    await interaction.response.send_message(embed=embed_commands, ephemeral=True)

async def get_dominant_color(url: str) -> int:
    # Получаем изображение аватара
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                image_data = await resp.read()
                # Загружаем изображение и извлекаем цвет
                image = Image.open(BytesIO(image_data))
                color_thief = ColorThief(BytesIO(image_data))
                # Извлекаем основной цвет
                dominant_color = color_thief.get_color(quality=1)
                return nextcord.Color.from_rgb(*dominant_color)
            else:
                return 0x223eff

@bot.slash_command(description="Показывает ваш уровень и количество сообщений, которые вы написали.")
async def profile(interaction: nextcord.Interaction):
    # Получаем данные пользователя из базы данных
    lvl_cursor.execute("SELECT lvl, messages FROM users WHERE id = ?", (interaction.user.id,))
    result = lvl_cursor.fetchone()

    if result is None:
        # Если пользователя нет в базе данных, добавляем его
        lvl_cursor.execute("INSERT INTO users (id, name, messages, lvl) VALUES (?, ?, 0, 0)",
                           (interaction.user.id, interaction.user.name))
        lvl_db.commit()
        await interaction.response.send_message("Вы ещё не написали ни одного сообщения!", ephemeral=True)
        return

    # Если пользователь есть в базе данных, извлекаем его данные
    lvl, messages = result
    lv_multiplier = (lvl * (lvl + 1)) // 2
    total_messages = (10 * lv_multiplier) + messages
    messages_to_next_level = 10 * (lvl + 1) - messages

    # Получаем доминирующий цвет аватара
    avatar_url = interaction.user.avatar.url
    accent_color = await get_dominant_color(avatar_url)

    # Создаем и отправляем сообщение с профилем
    embed = nextcord.Embed(
        title=f"Профиль {interaction.user.name}",
        description=f"Уровень: {lvl}\n"
                    f"Всего сообщений: {total_messages}\n"
                    f"Сообщений до следующего уровня: {messages_to_next_level}",
        color=accent_color
    )
    embed.set_thumbnail(url=avatar_url)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.slash_command(description="Показывает таблицу лидеров по уромню и количеству сообщений с их количеством"
                               " сообщений")
async def leaderboard(interaction: nextcord.Interaction):
    lvl_cursor.execute("SELECT * FROM users ORDER BY lvl DESC, messages DESC")
    result = lvl_cursor.fetchall()
    embed = nextcord.Embed(title="Таблица лидеров", description="Таблица лидеров по уровню и количеству сообщений.",
                           color=0x223eff)
    if len(result) < 10:
        for i in range(len(result)):
            lvl = result[i][2]
            messages = result[i][3]
            lvl_mult = (lvl * (lvl + 1)) // 2
            messages_count = (10 * lvl_mult) + messages
            if i == 0:
                embed.add_field(name=f"1. 🥇 {result[i][1]}", value=f"Уровень: {result[i][2]}\n"
                                                                   f"Количество сообщений: {messages_count}",
                                inline=False)
            elif i == 1:
                embed.add_field(name=f"2. 🥈 {result[i][1]}", value=f"Уровень: {result[i][2]}\n"
                                                                   f"Количество сообщений: {messages_count}",
                                inline=False)
            elif i == 2:
                embed.add_field(name=f"3. 🥉 {result[i][1]}", value=f"Уровень: {result[i][2]}\n"
                                                                   f"Количество сообщений: {messages_count}",
                                inline=False)
            else:
                embed.add_field(name=f"{i + 1}. {result[i][1]}", value=f"Уровень: {result[i][2]}\n"
                                                                       f"Количество сообщений: {messages_count}",
                                inline=False)
    else:
        for i in range(10):
            lvl = result[i][2]
            messages = result[i][3]
            lvl_mult = (lvl * (lvl + 1)) // 2
            messages_count = (10 * lvl_mult) + messages
            if i == 0:
                embed.add_field(name=f"1. 🥇 {result[i][1]}", value=f"Уровень: {result[i][2]}\n"
                                                                   f"Количество сообщений: {messages_count}",
                                inline=False)
            elif i == 1:
                embed.add_field(name=f"2. 🥈 {result[i][1]}", value=f"Уровень: {result[i][2]}\n"
                                                                   f"Количество сообщений: {messages_count}",
                                inline=False)
            elif i == 2:
                embed.add_field(name=f"3. 🥉 {result[i][1]}", value=f"Уровень: {result[i][2]}\n"
                                                                   f"Количество сообщений: {messages_count}",
                                inline=False)
            else:
                embed.add_field(name=f"{i + 1}. {result[i][1]}", value=f"Уровень: {result[i][2]}\n"
                                                                       f"Количество сообщений: {messages_count}",
                                inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.slash_command(description="Добавляет стримера в список уведомлений.")
async def add_streamer(interaction: nextcord.Interaction, streamer_nickname: str):
    # command should add a streamer to the database
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Вы не являетесь администратором, "
                                                "потому вы не можете использовать эту команду!", ephemeral=True)
    else:
        streamers_cursor.execute(f"SELECT nickname FROM streamers WHERE nickname = '{streamer_nickname}'")
        result = streamers_cursor.fetchone()
        if result is None:
            streamers_cursor.execute(f"INSERT INTO streamers (nickname) VALUES ('{streamer_nickname}')")
            streamers_db.commit()
            await interaction.response.send_message(
                f"Стример **{streamer_nickname}** был добавлен в список уведомлений!",
                ephemeral=True)
        else:
            await interaction.response.send_message(f"Стример **{streamer_nickname}** уже есть в списке уведомлений!",
                                                    ephemeral=True)


@bot.slash_command(description="Удаляет стримера из списка уведомлений.")
async def remove_streamer(interaction: nextcord.Interaction, streamer_nickname: str):
    # command should remove a streamer from the database
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Вы не являетесь администратором, "
                                                "потому вы не можете использовать эту команду!", ephemeral=True)
    else:
        streamers_cursor.execute(f"SELECT nickname FROM streamers WHERE nickname = '{streamer_nickname}'")
        result = streamers_cursor.fetchone()
        if result is not None:
            streamers_cursor.execute(f"DELETE FROM streamers WHERE nickname = '{streamer_nickname}'")
            streamers_db.commit()
            await interaction.response.send_message(
                f"Стример **{streamer_nickname}** был удален из списка уведомлений!",
                ephemeral=True)
        else:
            await interaction.response.send_message(f"Стример **{streamer_nickname}** не найден в списке уведомлений!",
                                                    ephemeral=True)


@bot.slash_command(description="Показывает список всех стримеров, которые есть в списке уведомлений.")
async def streamers(interaction: nextcord.Interaction):
    streamers_cursor.execute("SELECT nickname FROM streamers")
    result = streamers_cursor.fetchall()
    embed = nextcord.Embed(title="Список стримеров",
                           description="Список всех стримеров, которые есть в списке уведомлений.",
                           color=0x223eff)
    for i in range(len(result)):
        embed.add_field(name=f"{i + 1}. {result[i][0]}", value=f"Никнейм: {result[i][0]}", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tasks.loop(seconds=60)
async def twitchNotifications():
    # this function takes a streamer from the database and checks, if he is live
    global streamers_list
    for i in bot.guilds:
        streamers_cursor.execute('SELECT * FROM streamers')
        streamers_list = streamers_cursor.fetchall()
        for x in streamers_list:
            stream = checkIfLive(x[0])
            if stream != "OFFLINE":
                streamers_cursor.execute('SELECT status from streamers WHERE nickname = "%s"' % stream.streamer)
                result = streamers_cursor.fetchone()
                if result[0] == "OFFLINE" or result[0] is None:
                    if stream.game == "Just Chatting":
                        streamers_cursor.execute('UPDATE streamers SET status = "LIVE" WHERE nickname = "%s"'
                                                 % stream.streamer)
                        notification = nextcord.Embed(
                            title="Twitch",
                            description=f"Заходите на стрим {stream.streamer} прямо "
                                        f"[сейчас](https://www.twitch.tv/{stream.streamer})!!\n",
                            color=nextcord.Color.purple(),
                            timestamp=datetime.datetime.now()
                        )
                        notification.add_field(
                            name=stream.title,
                            value="Пока просто общаемся!"
                        )
                        notification.set_thumbnail(url=stream.thumbnail_url)
                        channel = bot.get_channel(notif_channel)
                        await channel.send("@everyone", embed=notification)
                    else:
                        streamers_cursor.execute('UPDATE streamers SET status = "LIVE" WHERE nickname = "%s"'
                                                 % stream.streamer)

                        notification = nextcord.Embed(
                            title="Twitch",
                            description=f"Заходите на стрим {stream.streamer} прямо "
                                        f"[сейчас](https://www.twitch.tv/{stream.streamer})!!\n",
                            color=nextcord.Color.purple(),
                            timestamp=datetime.datetime.now()
                        )
                        notification.add_field(
                            name=stream.title,
                            value=f"Стримим {stream.game}!"
                        )
                        notification.set_thumbnail(url=stream.thumbnail_url)
                        channel = bot.get_channel(notif_channel)
                        await channel.send("@everyone", embed=notification)
            else:
                streamers_cursor.execute('SELECT status from streamers WHERE nickname = "%s"' % x[0])
                result = streamers_cursor.fetchone()
                if result[0] == "LIVE":
                    streamers_cursor.execute('UPDATE streamers SET status = "OFFLINE" WHERE nickname = "%s"'
                                             % x[0])


@bot.slash_command(description="Удаляет все сообщения конкретного юзера в канале.")
async def delete_user_messages(interaction: nextcord.Interaction, user: nextcord.Member):
    messages = await interaction.channel.history().flatten()
    for message in messages:
        if message.author == user:
            await message.delete()
    await interaction.response.send_message(f"Все сообщения пользователя {user.mention} были удалены!", ephemeral=True)


bot.run(config['token'])  # bot runs up and gets a token from config file
