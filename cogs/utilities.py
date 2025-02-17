import random
import nextcord
from nextcord.ext import commands

class UtilitiesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(description="Показывает количество сообщений в канале")
    async def messages_count(self, interaction: nextcord.Interaction):
        count = 0
        async for message in interaction.channel.history(limit=100):
            count += 1
        await interaction.response.send_message(f"Количество сообщений в канале: {count}", ephemeral=True)

    @nextcord.slash_command(description="Показывает список всех команд в алфавитном порядке.")
    async def commands_list(self, interaction: nextcord.Interaction):
        commands_dict = {
            "/add_bad_word": "Добавляет плохое слово(плохие слова) в базу данных.",
            "/add_streamer": "Добавляет стримера в базу данных.",
            "/bad_words": "Показывает список всех плохих слов.",
            "/ban": "Банит участника сервера.",
            "/clear_all_warns": "Удаляет все предупреждения на сервере.",
            "/clear_warns": "Удаляет все предупреждения пользователя.",
            "/delete_message": "Удаляет определенное сообщение по id и выбранному каналу.",
            "/kick": "Кикает пользователя с сервера.",
            "/leaderboard": "Показывает таблицу лидеров по уровню и количеству сообщений.",
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
        embed = nextcord.Embed(
            title="Список всех команд",
            description="Список всех команд в алфавитном порядке.",
            color=0x223eff
        )
        for cmd, desc in sorted_commands.items():
            embed.add_field(name=cmd, value=desc, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @nextcord.slash_command(description="Добавляет плохое слово(плохие слова) в базу данных.")
    async def add_bad_word(self, interaction: nextcord.Interaction, word: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Вы не являетесь администратором, поэтому не можете использовать эту команду!", ephemeral=True)
            return
        cur = self.bot.db_bad_words.cursor()
        if "," in word:
            words = word.split(", ")
            for w in words:
                cur.execute("INSERT INTO bad_words (id, word) VALUES (?, ?)", (random.randint(1, 100000), w))
            self.bot.db_bad_words.commit()
            await interaction.response.send_message(f"Слова {words} были добавлены в базу данных!", ephemeral=True)
        else:
            cur.execute("INSERT INTO bad_words (id, word) VALUES (?, ?)", (random.randint(1, 100000), word))
            self.bot.db_bad_words.commit()
            await interaction.response.send_message(f"Слово {word} было добавлено в базу данных!", ephemeral=True)

    @nextcord.slash_command(description="Удаляет плохое слово из базы данных.")
    async def remove_bad_word(self, interaction: nextcord.Interaction, word: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Вы не являетесь администратором, поэтому не можете использовать эту команду!", ephemeral=True)
            return
        cur = self.bot.db_bad_words.cursor()
        cur.execute("DELETE FROM bad_words WHERE word = ?", (word,))
        self.bot.db_bad_words.commit()
        await interaction.response.send_message(f"Слово {word} было удалено из базы данных!", ephemeral=True)

    @nextcord.slash_command(description="Показывает список всех плохих слов.")
    async def bad_words(self, interaction: nextcord.Interaction):
        cur = self.bot.db_bad_words.cursor()
        cur.execute("SELECT word FROM bad_words")
        bad_words = cur.fetchall()
        embed = nextcord.Embed(
            title="Список плохих слов",
            description="Список всех плохих слов в базе данных.",
            color=0x223eff
        )
        for word in bad_words:
            embed.add_field(name="Слово", value=word[0], inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(UtilitiesCog(bot))
