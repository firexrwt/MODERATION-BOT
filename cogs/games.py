import random
import nextcord
from nextcord.ext import commands

class GamesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(description="Играет с вами в камень-ножницы-бумага.")
    async def rps(self, interaction: nextcord.Interaction, choice: str):
        choices = ["камень", "бумага", "ножницы"]
        choice = choice.lower()
        if choice not in choices:
            await interaction.response.send_message("Вы должны выбрать из вариантов: камень, бумага, ножницы", ephemeral=True)
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

def setup(bot):
    bot.add_cog(GamesCog(bot))
