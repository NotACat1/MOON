import discord
from discord.ext import commands
from config.settings import LOBBY_CHANNELS, CATEGORY_IDS, ROOM_NAME_TEMPLATE
import asyncio

# =============================================================================
# ГЛОБАЛЬНОЕ ХРАНИЛИЩЕ ВРЕМЕННЫХ КАНАЛОВ
# =============================================================================
temp_channels = set()  # Множество для хранения ID созданных временных каналов

class VoiceManager(commands.Cog):
    """Cog для управления автоматическим созданием и удалением временных голосовых каналов."""
    
    def __init__(self, bot: commands.Bot):
        """
        Инициализация модуля управления голосовыми каналами.
        
        Args:
            bot: Экземпляр Discord бота
        """
        self.bot = bot
        self._pending_deletion = set()  # Множество для отслеживания каналов в процессе удаления

    async def safe_channel_delete(self, channel: discord.VoiceChannel):
        """
        Безопасно удаляет временный канал с обработкой ошибок.
        
        Args:
            channel: Голосовой канал для удаления
        """
        if channel.id not in temp_channels:
            return
            
        try:
            # Проверяем, что канал действительно пуст
            if len(channel.members) == 0:
                await channel.delete(reason="Автоматическое удаление пустой временной комнаты")
                temp_channels.discard(channel.id)
                print(f"🗑️ Удалена пустая комната: {channel.name} (ID: {channel.id})")
        except discord.NotFound:
            # Канал уже удален
            temp_channels.discard(channel.id)
        except discord.Forbidden:
            print(f"❌ Ошибка прав: Не удалось удалить комнату {channel.name}")
        except Exception as e:
            print(f"❌ Неожиданная ошибка при удалении комнаты {channel.name}: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, 
                                  before: discord.VoiceState, 
                                  after: discord.VoiceState):
        """
        Обрабатывает события изменения голосового состояния пользователей.
        
        Args:
            member: Пользователь, изменивший состояние
            before: Предыдущее голосовое состояние
            after: Новое голосовое состояние
        """
        # =====================================================================
        # СОЗДАНИЕ НОВОЙ КОМНАТЫ ПРИ ЗАХОДЕ В ЛОББИ
        # =====================================================================
        if after.channel and after.channel.id in LOBBY_CHANNELS.values():
            print(f"👤 Пользователь {member.display_name} зашел в лобби: {after.channel.name}")
            
            # Определяем тип лобби
            lobby_type = None
            for key, lobby_id in LOBBY_CHANNELS.items():
                if after.channel.id == lobby_id:
                    lobby_type = key
                    break

            if not lobby_type:
                print(f"⚠ Неизвестное лобби: {after.channel.id}")
                return

            # Получаем ID категории для этого типа лобби
            category_id = CATEGORY_IDS.get(lobby_type)
            if not category_id:
                print(f"⚠ Для лобби '{lobby_type}' не указана категория в настройках")
                return
                
            # Находим категорию на сервере
            category = discord.utils.get(member.guild.categories, id=category_id)
            if not category:
                print(f"⚠ Категория {lobby_type} (ID: {category_id}) не найдена на сервере")
                return

            try:
                # Создаем overwrites для правильных прав доступа
                overwrites = {
                    member.guild.default_role: discord.PermissionOverwrite(
                        connect=True,
                        view_channel=True
                    ),
                    member.guild.me: discord.PermissionOverwrite(
                        manage_channels=True,
                        manage_roles=True,
                        connect=True,
                        view_channel=True
                    ),
                    member: discord.PermissionOverwrite(
                        manage_channels=True,
                        connect=True,
                        view_channel=True
                    )
                }
                
                # Генерируем название комнаты по шаблону
                name_template = ROOM_NAME_TEMPLATE.get(lobby_type, "Комната {user}")
                channel_name = name_template.format(user=member.display_name)
                
                # Создаем новый голосовой канал
                new_channel = await category.create_voice_channel(
                    name=channel_name,
                    user_limit=0,  # Без лимита по умолчанию
                    overwrites=overwrites,
                    reason=f"Автоматическое создание комнаты для {member.display_name}"
                )
                
                # Добавляем канал в отслеживаемые
                temp_channels.add(new_channel.id)
                
                print(f"✅ Создана новая комната: {channel_name} (ID: {new_channel.id})")
                print(f"📊 Всего активных комнат: {len(temp_channels)}")

                # Перемещаем пользователя в новую комнату
                await member.move_to(new_channel)
                print(f"👤 Пользователь {member.display_name} перемещен в свою комнату")
                
            except discord.Forbidden:
                print(f"❌ Ошибка прав: Бот не может создавать каналы в категории {category.name}")
            except Exception as e:
                print(f"❌ Ошибка при создании комнаты: {e}")

        # =====================================================================
        # ПРОВЕРКА И УДАЛЕНИЕ ПУСТЫХ КОМНАТ
        # =====================================================================
        if before.channel and before.channel.id in temp_channels:
            # Используем задержку для избежания race condition
            await asyncio.sleep(2)  # Ждем 2 секунды перед проверкой
            
            try:
                # Перепроверяем канал (может быть уже удален)
                channel = self.bot.get_channel(before.channel.id)
                if channel and len(channel.members) == 0 and channel.id not in self._pending_deletion:
                    self._pending_deletion.add(channel.id)
                    await self.safe_channel_delete(channel)
                    self._pending_deletion.discard(channel.id)
            except:
                # Игнорируем ошибки при повторной проверке
                pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """
        Обрабатывает выход пользователя с сервера (включая бан/кик).
        
        Args:
            member: Пользователь, покинувший сервер
        """
        if member.voice and member.voice.channel:
            channel = member.voice.channel
            if channel.id in temp_channels:
                print(f"👤 Пользователь {member.display_name} покинул сервер из комнаты {channel.name}")
                await self.safe_channel_delete(channel)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """
        Обрабатывает бан пользователя на сервере.
        
        Args:
            guild: Сервер, где произошел бан
            user: Забаненный пользователь
        """
        member = guild.get_member(user.id)
        if member and member.voice and member.voice.channel:
            channel = member.voice.channel
            if channel.id in temp_channels:
                print(f"🔨 Пользователь {member.display_name} забанен в комнате {channel.name}")
                await self.safe_channel_delete(channel)

async def setup(bot: commands.Bot):
    """
    Функция setup для загрузки кога в бота.
    
    Args:
        bot: Экземпляр Discord бота
    """
    await bot.add_cog(VoiceManager(bot))