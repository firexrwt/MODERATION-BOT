import random
import nextcord
from nextcord.ext import commands

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Получаем список плохих слов из базы данных
        cur = self.bot.db_bad_words.cursor()
        cur.execute("SELECT word FROM bad_words")
        bad_words_list = {word[0] for word in cur.fetchall()}

        if not any(role.name in self.bot.admin_roles for role in message.author.roles):
            if any(word in message.content.lower().split() for word in bad_words_list):
                try:
                    await message.delete()
                except nextcord.Forbidden:
                    pass
                log_channel = self.bot.get_channel(self.bot.logs_channel)
                warn_cur = self.bot.db_warnings.cursor()
                warn_cur.execute("SELECT warns FROM users WHERE id = ?", (message.author.id,))
                result = warn_cur.fetchone()
                if result is None:
                    warn_cur.execute("INSERT INTO users (id, username, warns) VALUES (?, ?, ?)",
                                     (message.author.id, message.author.name, 1))
                    self.bot.db_warnings.commit()
                    if log_channel:
                        await log_channel.send(
                            f"{message.author.mention} написал плохие слова! Сообщение удалено. Причина: Плохие слова.")
                else:
                    warns = result[0] + 1
                    warn_cur.execute("UPDATE users SET warns = ? WHERE id = ?", (warns, message.author.id))
                    self.bot.db_warnings.commit()
                    if log_channel:
                        if warns >= 3:
                            try:
                                await message.author.send("Вы были забанены за плохие слова!")
                            except:
                                pass
                            await log_channel.send(
                                f"{message.author.mention} написал плохие слова 3 раза! Сообщение удалено и пользователь забанен. Причина: Плохие слова.")
                            try:
                                await message.author.ban(reason="Плохие слова")
                                await message.channel.purge(limit=100, check=lambda m: m.author == message.author, bulk=True)
                            except nextcord.Forbidden:
                                pass
                            lvl_cur = self.bot.db_lvl.cursor()
                            lvl_cur.execute("DELETE FROM users WHERE id = ?", (message.author.id,))
                            self.bot.db_lvl.commit()
                        else:
                            try:
                                await message.author.send("Не пишите плохие слова!!!")
                            except:
                                pass
                            await log_channel.send(
                                f"{message.author.mention} написал плохие слова! Сообщение удалено. Причина: Плохие слова.")

    @nextcord.slash_command(description="Кикает пользователя с сервера.")
    async def kick(self, interaction: nextcord.Interaction, user: nextcord.Member, reason: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Вы не являетесь администратором, поэтому не можете использовать эту команду!", ephemeral=True)
            return
        await interaction.response.send_message(f"{user.mention} был кикнут!", ephemeral=True)
        log_channel = self.bot.get_channel(self.bot.logs_channel)
        if log_channel:
            await log_channel.send(f"{user.mention} был кикнут администратором {interaction.user.mention}. Причина: {reason}")
        try:
            await user.kick(reason=reason)
        except nextcord.Forbidden:
            await interaction.followup.send("Не удалось кикнуть пользователя.", ephemeral=True)

    @nextcord.slash_command(description="Банит участника сервера.")
    async def ban(self, interaction: nextcord.Interaction, user: nextcord.Member, reason: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Вы не являетесь администратором, поэтому не можете использовать эту команду!", ephemeral=True)
            return
        await interaction.response.send_message(f"{user.mention} был забанен!", ephemeral=True)
        try:
            await user.send(f"Вы были забанены!\nПричина: {reason}")
        except:
            pass
        log_channel = self.bot.get_channel(self.bot.logs_channel)
        if log_channel:
            await log_channel.send(f"{user.mention} был забанен администратором {interaction.user.mention}. Причина: {reason}")
        try:
            await user.ban(reason=reason)
        except nextcord.Forbidden:
            await interaction.followup.send("Не удалось забанить пользователя.", ephemeral=True)

    @nextcord.slash_command(description="Не даёт человеку писать на сервере некоторое время.")
    async def mute(self, interaction: nextcord.Interaction, user: nextcord.Member, duration: str, reason: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Вы не являетесь администратором, поэтому не можете использовать эту команду!", ephemeral=True)
            return
        import humanfriendly
        try:
            duration_sec = humanfriendly.parse_timespan(duration)
        except ValueError:
            await interaction.response.send_message("Некорректный формат времени. Используйте, например, '10s' или '5m'.", ephemeral=True)
            return
        mute_end_time = nextcord.utils.utcnow() + nextcord.timedelta(seconds=duration_sec)
        try:
            await user.edit(timeout=mute_end_time)
        except nextcord.Forbidden:
            await interaction.response.send_message("Не удалось замутить пользователя.", ephemeral=True)
            return
        log_channel = self.bot.get_channel(self.bot.logs_channel)
        if log_channel:
            await log_channel.send(f"{user.mention} был замучен администратором {interaction.user.mention} на {duration}. Причина: {reason}.")
        await interaction.response.send_message(f"{user.mention} был замучен на {duration}!", ephemeral=True)

    @nextcord.slash_command(description="Возвращает возможность писать в чат выбранному участнику сервера.")
    async def unmute(self, interaction: nextcord.Interaction, user: nextcord.Member, reason: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Вы не являетесь администратором, поэтому не можете использовать эту команду!", ephemeral=True)
            return
        try:
            await user.edit(timeout=None)
        except nextcord.Forbidden:
            await interaction.response.send_message("Не удалось размутить пользователя.", ephemeral=True)
            return
        log_channel = self.bot.get_channel(self.bot.logs_channel)
        if log_channel:
            await log_channel.send(f"{user.mention} был размучен администратором {interaction.user.mention}. Причина: {reason}.")
        await interaction.response.send_message(f"{user.mention} был размучен!", ephemeral=True)

    @nextcord.slash_command(description="Удаляет определенное сообщение по id и выбранному каналу.")
    async def delete_message(self, interaction: nextcord.Interaction, channel: nextcord.TextChannel, message_id: int, reason: str):
        try:
            msg = await channel.fetch_message(message_id)
        except:
            await interaction.response.send_message("Сообщение не найдено.", ephemeral=True)
            return
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Вы не являетесь администратором, поэтому не можете использовать эту команду!", ephemeral=True)
            return
        await interaction.response.send_message(f"Сообщение пользователя {msg.author.mention} было удалено!", ephemeral=True)
        log_channel = self.bot.get_channel(self.bot.logs_channel)
        if log_channel:
            await log_channel.send(f"{msg.author.mention} написал сообщение, которое было удалено администратором {interaction.user.mention}. Причина: {reason}.")
        try:
            await msg.delete()
        except nextcord.Forbidden:
            await interaction.followup.send("Не удалось удалить сообщение.", ephemeral=True)

    @nextcord.slash_command(description="Показывает список предупреждений пользователя.")
    async def warns(self, interaction: nextcord.Interaction, user: nextcord.Member):
        if not interaction.user.guild_permissions.administrator and interaction.user != user:
            await interaction.response.send_message("Вы не являетесь администратором и не можете просматривать предупреждения других пользователей.", ephemeral=True)
            return
        cur = self.bot.db_warnings.cursor()
        cur.execute("SELECT warns FROM users WHERE id = ?", (user.id,))
        result = cur.fetchone()
        warns_count = result[0] if result else 0
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

    @nextcord.slash_command(description="Выдаёт предупреждение пользователю.")
    async def warn(self, interaction: nextcord.Interaction, user: nextcord.Member, reason: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Вы не являетесь администратором, поэтому не можете использовать эту команду!", ephemeral=True)
            return
        await interaction.response.send_message(f"Пользователь {user.mention} получил предупреждение!", ephemeral=True)
        log_channel = self.bot.get_channel(self.bot.logs_channel)
        if log_channel:
            await log_channel.send(f"{user.mention} получил предупреждение от {interaction.user.mention}. Причина: {reason}.")
        cur = self.bot.db_warnings.cursor()
        cur.execute("SELECT id FROM users WHERE id = ?", (user.id,))
        result = cur.fetchone()
        if result is None:
            cur.execute("INSERT INTO users (id, username, warns) VALUES (?, ?, ?)", (user.id, user.name, 1))
        else:
            cur.execute("SELECT warns FROM users WHERE id = ?", (user.id,))
            result = cur.fetchone()
            warns_count = result[0] + 1
            cur.execute("UPDATE users SET warns = ? WHERE id = ?", (warns_count, user.id))
        self.bot.db_warnings.commit()

    @nextcord.slash_command(description="Удаляет все предупреждения пользователя.")
    async def clear_warns(self, interaction: nextcord.Interaction, user: nextcord.Member, reason: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Вы не являетесь администратором, поэтому не можете использовать эту команду!", ephemeral=True)
            return
        cur = self.bot.db_warnings.cursor()
        cur.execute("UPDATE users SET warns = 0 WHERE id = ?", (user.id,))
        self.bot.db_warnings.commit()
        log_channel = self.bot.get_channel(self.bot.logs_channel)
        if log_channel:
            await log_channel.send(f"Все предупреждения пользователя {user.mention} были удалены администратором {interaction.user.mention}. Причина: {reason}.")
        await interaction.response.send_message(f"Все предупреждения пользователя {user.mention} были удалены!", ephemeral=True)

    @nextcord.slash_command(description="Удаляет все предупреждения на сервере.")
    async def clear_all_warns(self, interaction: nextcord.Interaction, reason: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Вы не являетесь администратором, поэтому не можете использовать эту команду!", ephemeral=True)
            return
        cur = self.bot.db_warnings.cursor()
        cur.execute("UPDATE users SET warns = 0")
        self.bot.db_warnings.commit()
        log_channel = self.bot.get_channel(self.bot.logs_channel)
        if log_channel:
            await log_channel.send(f"Все предупреждения на сервере были удалены администратором {interaction.user.mention}. Причина: {reason}.")
        await interaction.response.send_message("Все предупреждения на сервере были удалены!", ephemeral=True)

    @nextcord.slash_command(description="Разбанивает пользователя по id.")
    async def unban(self, interaction: nextcord.Interaction, user_id: int, reason: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Вы не являетесь администратором, поэтому не можете использовать эту команду!", ephemeral=True)
            return
        try:
            await interaction.guild.unban(nextcord.Object(id=user_id), reason=reason)
        except Exception:
            await interaction.response.send_message("Не удалось разбанить пользователя.", ephemeral=True)
            return
        cur = self.bot.db_warnings.cursor()
        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.bot.db_warnings.commit()
        log_channel = self.bot.get_channel(self.bot.logs_channel)
        if log_channel:
            await log_channel.send(f"<@{user_id}> был разбанен администратором {interaction.user.mention}. Причина: {reason}")
        await interaction.response.send_message(f"Пользователь с id {user_id} был разбанен!", ephemeral=True)

    @nextcord.slash_command(description="Удаляет все сообщения конкретного юзера в канале.")
    async def delete_user_messages(self, interaction: nextcord.Interaction, user: nextcord.Member):
        messages = await interaction.channel.history(limit=100).flatten()
        for msg in messages:
            if msg.author == user:
                try:
                    await msg.delete()
                except:
                    continue
        await interaction.response.send_message(f"Все сообщения пользователя {user.mention} были удалены!", ephemeral=True)

def setup(bot):
    bot.add_cog(ModerationCog(bot))
