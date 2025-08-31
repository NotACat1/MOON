import discord
from discord.ext import commands
from config.settings import DISCORD_TOKEN

# Настройка intents
intents = discord.Intents.default()
intents.members = True  # Привилегированный интент
intents.message_content = True  # Для работы с содержимым сообщений

# Создаем бота только ОДИН раз
bot = commands.Bot(command_prefix="!", intents=intents)

initial_extensions = ["cogs.voice_manager", "cogs.commands"]

@bot.event
async def on_ready():
    print(f"✅ Бот запущен как {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔧 Синхронизировано {len(synced)} команд")
    except Exception as e:
        print(f"Ошибка при синхронизации команд: {e}")

# Правильная загрузка расширений с использованием setup_hook
async def setup_hook():
    for ext in initial_extensions:
        try:
            await bot.load_extension(ext)
            print(f"✅ Загружено расширение: {ext}")
        except Exception as e:
            print(f"❌ Ошибка загрузки {ext}: {e}")

# Устанавливаем хук
bot.setup_hook = setup_hook

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)