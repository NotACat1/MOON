import discord
from discord import app_commands
from discord.ext import commands
from .voice_manager import temp_channels
import asyncio

# =============================================================================
# КОНСТАНТЫ ДЛЯ ЦВЕТОВОГО КОДИРОВАНИЯ СООБЩЕНИЙ
# =============================================================================
SUCCESS_COLOR = discord.Color.green()      # Успешные операции
ERROR_COLOR = discord.Color.red()          # Ошибки и предупреждения
INFO_COLOR = discord.Color.blurple()       # Информационные сообщения
WARNING_COLOR = discord.Color.orange()     # Предупреждения

class ChannelCommands(commands.Cog):
    """Cog для управления командами временных голосовых каналов."""
    
    def __init__(self, bot: commands.Bot):
        """
        Инициализация модуля команд.
        
        Args:
            bot: Экземпляр Discord бота
        """
        self.bot = bot

    def get_user_channel(self, interaction: discord.Interaction) -> discord.VoiceChannel | None:
        """
        Проверяет, находится ли пользователь в своем временном канале.
        
        Args:
            interaction: Объект взаимодействия Discord
            
        Returns:
            VoiceChannel объект или None если пользователь не в своем канале
        """
        if not interaction.user.voice:
            return None
            
        channel = interaction.user.voice.channel
        return channel if channel and channel.id in temp_channels else None

    # =========================================================================
    # УТИЛИТАРНЫЕ КОМАНДЫ
    # =========================================================================

    @app_commands.command(
        name="help", 
        description="📚 Показать список всех доступных команд для управления комнатой"
    )
    async def help_cmd(self, interaction: discord.Interaction):
        """
        Отображает интерактивное руководство по командам бота.
        
        Args:
            interaction: Объект взаимодействия Discord
        """
        embed = discord.Embed(
            title="🎮 **Центр управления комнатами**",
            description=(
                "Добро пожаловать в систему управления временными комнатами! "
                "Здесь вы можете настроить свою комнату под любые нужды.\n\n"
                "**✨ Доступные команды:**"
            ),
            color=INFO_COLOR
        )
        
        # Команды с эмодзи и подробными описаниями
        commands_info = [
            ("🏷️ `/setname <название>`", "Задайте уникальное имя для вашей комнаты\n*Максимум 50 символов*"),
            ("👥 `/setlimit <число>`", "Установите лимит участников (0-99)\n*0 = без ограничений*"),
            ("🔒 `/private on/off`", "Контролируйте доступ к вашей комнате\n*Приватный/публичный режим*"),
            ("📊 `/ping`", "Проверьте скорость отклика бота и состояние системы"),
            ("🛠️ `/permissions`", "Проверить права бота на управление комнатой")
        ]
        
        for name, value in commands_info:
            embed.add_field(name=name, value=value, inline=False)
        
        embed.add_field(
            name="💡 **Важно**",
            value=(
                "• Все команды работают только из вашей временной комнаты\n"
                "• Для приватных комнат используйте правый клик → 'Пригласить в канал'\n"
                "• Автоматическое удаление пустых комнат через 60 секунд"
            ),
            inline=False
        )
        
        embed.set_footer(
            text="🚀 Создавайте уютные пространства для общения, игр и работы!",
            icon_url="https://cdn.discordapp.com/emojis/892292100084310086.webp"
        )
        
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/892292100084310086.webp")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="ping", 
        description="📊 Проверить скорость отклика бота и состояние системы"
    )
    async def ping(self, interaction: discord.Interaction):
        """
        Проверяет задержку бота и отображает статус системы.
        
        Args:
            interaction: Объект взаимодействия Discord
        """
        latency = round(self.bot.latency * 1000)
        
        # Определяем цвет в зависимости от задержки
        if latency < 100:
            color = SUCCESS_COLOR
            status = "📶 Отличное соединение"
            emoji = "⚡"
        elif latency < 300:
            color = INFO_COLOR
            status = "📶 Хорошее соединение"
            emoji = "✅"
        else:
            color = WARNING_COLOR
            status = "📶 Высокая задержка"
            emoji = "⚠️"
        
        embed = discord.Embed(
            title=f"{emoji} Статистика системы",
            color=color
        )
        
        embed.add_field(name="🏓 Задержка бота", value=f"**{latency}ms**", inline=True)
        embed.add_field(name="📈 Статус соединения", value=status, inline=True)
        embed.add_field(name="🎯 Активных комнат", value=f"**{len(temp_channels)}**", inline=True)
        
        embed.add_field(
            name="🛠️ Состояние системы", 
            value="Все системы работают в штатном режиме" if latency < 500 else "Рекомендуется проверить соединение",
            inline=False
        )
        
        embed.set_footer(text="🤖 Бот готов к работе и ожидает ваших команд!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # =========================================================================
    # ОСНОВНЫЕ КОМАНДЫ УПРАВЛЕНИЯ КОМНАТАМИ
    # =========================================================================

    @app_commands.command(
        name="setname", 
        description="🏷️ Изменить название вашей временной комнаты"
    )
    @app_commands.describe(name="Новое название комнаты (1-50 символов)")
    async def setname(self, interaction: discord.Interaction, name: str):
        """
        Изменяет название временной голосовой комнаты.
        
        Args:
            interaction: Объект взаимодействия Discord
            name: Новое название комнаты
        """
        channel = self.get_user_channel(interaction)
        if not channel:
            embed = discord.Embed(
                title="❌ **Доступ запрещен**",
                description=(
                    "Эта команда доступна только в вашей временной комнате!\n\n"
                    "**Чтобы использовать команду:**\n"
                    "1. Создайте комнату, зайдя в любое лобби\n"
                    "2. Находясь в своей комнате, используйте команду повторно"
                ),
                color=ERROR_COLOR
            )
            embed.set_footer(text="💡 Лобби: Допросная, Митинг, Игры, Кинозал, Переговорная")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # Валидация длины названия
        if len(name) < 1 or len(name) > 50:
            embed = discord.Embed(
                title="⚠️ **Некорректное название**",
                description=(
                    "Название комнаты должно содержать от **1 до 50 символов**.\n\n"
                    f"**Текущая длина:** {len(name)} символов\n"
                    "**Рекомендация:** Используйте короткое и понятное название"
                ),
                color=ERROR_COLOR
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            # Изменяем название канала
            await channel.edit(name=name)
            
            embed = discord.Embed(
                title="✅ **Название обновлено!**",
                description=(
                    f"Ваша комната теперь называется:\n"
                    f"## 🏷️ {discord.utils.escape_markdown(name)}\n\n"
                    "✨ Название успешно изменено и видно всем участникам сервера."
                ),
                color=SUCCESS_COLOR
            )
            embed.set_footer(text="🎉 Отличный выбор названия!")
            
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="🔐 **Ошибка прав доступа**",
                description=(
                    "Бот не имеет прав для изменения названия канала!\n\n"
                    "**Необходимые права:**\n"
                    "• Управление каналами (Manage Channels)\n"
                    "• Просмотр каналов (View Channel)"
                ),
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="⚡ **Неожиданная ошибка**",
                description=f"Произошла ошибка при изменении названия: ```{str(e)}```",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="setlimit", 
        description="👥 Установить лимит участников в комнате (0 = без лимита)"
    )
    @app_commands.describe(limit="Количество участников (0-99)")
    async def setlimit(self, interaction: discord.Interaction, limit: int):
        """
        Устанавливает лимит участников для временной комнаты.
        
        Args:
            interaction: Объект взаимодействия Discord
            limit: Лимит участников (0-99)
        """
        channel = self.get_user_channel(interaction)
        if not channel:
            embed = discord.Embed(
                title="❌ **Доступ запрещен**",
                description="Эта команда доступна только в вашей временной комнате!",
                color=ERROR_COLOR
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # Валидация лимита
        if not (0 <= limit <= 99):
            embed = discord.Embed(
                title="⚠️ **Некорректный лимит**",
                description=(
                    "Лимит участников должен быть в диапазоне **от 0 до 99**.\n\n"
                    "**Примеры использования:**\n"
                    "• `0` - Без ограничений (по умолчанию)\n"
                    "• `5` - До 5 участников\n"
                    "• `10` - До 10 участников"
                ),
                color=ERROR_COLOR
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            # Устанавливаем лимит
            await channel.edit(user_limit=limit)
            
            # Форматируем текст лимита
            limit_text = (
                "♾️ **Без ограничений**" if limit == 0 
                else f"👥 **До {limit} участников**"
            )
            
            embed = discord.Embed(
                title="✅ **Лимит установлен!**",
                description=(
                    f"{limit_text}\n\n"
                    "Теперь ваша комната имеет новые ограничения по количеству участников. "
                    "При достижении лимита новые участники не смогут подключиться."
                ),
                color=SUCCESS_COLOR
            )
            
            if limit > 0:
                embed.add_field(
                    name="💡 Совет", 
                    value="Для отмены лимита используйте `/setlimit 0`", 
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="🔐 **Ошибка прав доступа**",
                description="Бот не имеет прав для изменения лимита участников!",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="private", 
        description="🔒 Переключить приватный режим комнаты (on/off)"
    )
    @app_commands.describe(mode="Режим: 'on' для приватности, 'off' для публичности")
    async def private(self, interaction: discord.Interaction, mode: str):
        """
        Переключает режим приватности временной комнаты.
        
        Args:
            interaction: Объект взаимодействия Discord
            mode: Режим работы ('on' или 'off')
        """
        channel = self.get_user_channel(interaction)
        if not channel:
            embed = discord.Embed(
                title="❌ **Доступ запрещен**",
                description="Эта команда доступна только в вашей временной комнате!",
                color=ERROR_COLOR
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            if mode.lower() == "on":
                # Включаем приватный режим
                overwrite = discord.PermissionOverwrite()
                overwrite.connect = False  # Запрещаем подключение по умолчанию
                overwrite.view_channel = True  # Разрешаем просмотр
                
                await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
                
                # Даем создателю полные права
                creator_overwrite = discord.PermissionOverwrite(
                    connect=True,
                    view_channel=True,
                    manage_channels=True
                )
                await channel.set_permissions(interaction.user, overwrite=creator_overwrite)
                
                embed = discord.Embed(
                    title="🔒 **Приватный режим активирован!**",
                    description=(
                        "Ваша комната теперь доступна только по приглашению!\n\n"
                        "**Как пригласить участников:**\n"
                        "1. Правый клик на пользователе\n"
                        "2. Выберите 'Пригласить в канал'\n"
                        "3. Участник получит приглашение"
                    ),
                    color=SUCCESS_COLOR
                )
                embed.set_footer(text="💎 Только для избранных!")
                
            elif mode.lower() == "off":
                # Выключаем приватный режим
                await channel.set_permissions(interaction.guild.default_role, overwrite=None)
                
                embed = discord.Embed(
                    title="🌍 **Публичный режим активирован!**",
                    description=(
                        "Ваша комната теперь доступна всем участникам сервера!\n\n"
                        "Любой пользователь может свободно подключаться к вашей комнате "
                        "без необходимости приглашения."
                    ),
                    color=SUCCESS_COLOR
                )
                embed.set_footer(text="🎉 Добро пожаловать всем!")
                
            else:
                embed = discord.Embed(
                    title="⚠️ **Неверный параметр**",
                    description=(
                        "Используйте корректные значения:\n\n"
                        "• `/private on` - Включить приватный режим\n"
                        "• `/private off` - Выключить приватный режим"
                    ),
                    color=ERROR_COLOR
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
            
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="🔐 **Критическая ошибка прав**",
                description=(
                    "Бот не имеет необходимых прав для управления доступом!\n\n"
                    "**Требуемые права:**\n"
                    "• Управление ролями (Manage Roles)\n"
                    "• Управление каналами (Manage Channels)\n"
                    "• Просмотр журнала аудита (View Audit Log)"
                ),
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    """
    Функция setup для загрузки кога в бота.
    
    Args:
        bot: Экземпляр Discord бота
    """
    await bot.add_cog(ChannelCommands(bot))