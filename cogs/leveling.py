import datetime
import nextcord
from nextcord.ext import commands, tasks
from io import BytesIO
import aiohttp
from PIL import Image
from colorthief import ColorThief

class LevelingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_lvl_roles_task.start()

    def cog_unload(self):
        self.check_lvl_roles_task.cancel()

    async def update_member_roles(self, member, lvl):
        for role_name, required_lvl in self.bot.lvl_roles.items():
            role = nextcord.utils.get(member.guild.roles, name=role_name)
            if role:
                if lvl >= required_lvl and role not in member.roles:
                    try:
                        await member.add_roles(role)
                    except Exception:
                        pass
                elif lvl < required_lvl and role in member.roles:
                    try:
                        await member.remove_roles(role)
                    except Exception:
                        pass

    @tasks.loop(minutes=1)
    async def check_lvl_roles_task(self):
        for guild in self.bot.guilds:
            for member in guild.members:
                if not member.bot:
                    cur = self.bot.db_lvl.cursor()
                    cur.execute("SELECT lvl FROM users WHERE id = ?", (member.id,))
                    result = cur.fetchone()
                    if result is not None:
                        lvl = result[0]
                        await self.update_member_roles(member, lvl)
                else:
                    for role_name in self.bot.lvl_roles:
                        role = nextcord.utils.get(guild.roles, name=role_name)
                        if role in member.roles:
                            try:
                                await member.remove_roles(role)
                            except Exception:
                                pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if (message.channel.category and message.channel.category.id not in self.bot.exclude_categories and
            message.channel.id not in self.bot.exclude_channels and not message.content.startswith("/")):
            cur = self.bot.db_lvl.cursor()
            cur.execute("SELECT messages, lvl FROM users WHERE id = ?", (message.author.id,))
            result = cur.fetchone()
            if result is None:
                cur.execute("INSERT INTO users (id, username, messages, lvl) VALUES (?, ?, 1, 0)",
                            (message.author.id, message.author.name))
                self.bot.db_lvl.commit()
            else:
                messages_count, lvl = result
                messages_count += 1
                cur.execute("UPDATE users SET messages = ? WHERE id = ?", (messages_count, message.author.id))
                self.bot.db_lvl.commit()
                if messages_count >= 10 * (lvl + 1):
                    lvl += 1
                    cur.execute("UPDATE users SET lvl = ?, messages = 0 WHERE id = ?", (lvl, message.author.id))
                    self.bot.db_lvl.commit()
                    lvl_channel = self.bot.get_channel(self.bot.new_lvl_channel)
                    if lvl_channel:
                        embed = nextcord.Embed(
                            title="Поздравляем!",
                            description=f"{message.author.mention} получил {lvl} уровень!"
                        )
                        await lvl_channel.send(embed=embed)
                    await self.update_member_roles(message.author, lvl)

    @nextcord.slash_command(description="Показывает ваш уровень и количество сообщений, которые вы написали.")
    async def profile(self, interaction: nextcord.Interaction):
        cur = self.bot.db_lvl.cursor()
        cur.execute("SELECT lvl, messages FROM users WHERE id = ?", (interaction.user.id,))
        result = cur.fetchone()
        if result is None:
            cur.execute("INSERT INTO users (id, username, messages, lvl) VALUES (?, ?, 0, 0)",
                        (interaction.user.id, interaction.user.name))
            self.bot.db_lvl.commit()
            await interaction.response.send_message("Вы ещё не написали ни одного сообщения!", ephemeral=True)
            return
        lvl, messages = result
        lv_multiplier = (lvl * (lvl + 1)) // 2
        total_messages = (10 * lv_multiplier) + messages
        messages_to_next_level = 10 * (lvl + 1) - messages

        # Определяем доминирующий цвет аватара
        async with aiohttp.ClientSession() as session:
            async with session.get(interaction.user.avatar.url) as resp:
                if resp.status == 200:
                    image_data = await resp.read()
                    color_thief = ColorThief(BytesIO(image_data))
                    dominant_color = color_thief.get_color(quality=1)
                    accent_color = nextcord.Color.from_rgb(*dominant_color)
                else:
                    accent_color = nextcord.Color(0x223eff)

        embed = nextcord.Embed(
            title=f"Профиль {interaction.user.name}",
            description=f"Уровень: {lvl}\nВсего сообщений: {total_messages}\nСообщений до следующего уровня: {messages_to_next_level}",
            color=accent_color
        )
        embed.set_thumbnail(url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @nextcord.slash_command(description="Показывает таблицу лидеров по уровню и количеству сообщений.")
    async def leaderboard(self, interaction: nextcord.Interaction):
        cur = self.bot.db_lvl.cursor()
        cur.execute("SELECT * FROM users ORDER BY lvl DESC, messages DESC")
        result = cur.fetchall()
        embed = nextcord.Embed(
            title="Таблица лидеров",
            description="Таблица лидеров по уровню и количеству сообщений.",
            color=0x223eff
        )
        for i, row in enumerate(result[:10]):
            lvl = row[2]
            messages = row[3]
            lvl_mult = (lvl * (lvl + 1)) // 2
            messages_count = (10 * lvl_mult) + messages
            if i == 0:
                embed.add_field(name=f"1. 🥇 {row[1]}", value=f"Уровень: {lvl}\nКоличество сообщений: {messages_count}", inline=False)
            elif i == 1:
                embed.add_field(name=f"2. 🥈 {row[1]}", value=f"Уровень: {lvl}\nКоличество сообщений: {messages_count}", inline=False)
            elif i == 2:
                embed.add_field(name=f"3. 🥉 {row[1]}", value=f"Уровень: {lvl}\nКоличество сообщений: {messages_count}", inline=False)
            else:
                embed.add_field(name=f"{i+1}. {row[1]}", value=f"Уровень: {lvl}\nКоличество сообщений: {messages_count}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(LevelingCog(bot))
