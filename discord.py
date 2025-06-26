import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Конфигурация (можно вынести в отдельный файл)
WARN_LIMIT = 3     # Макс кол-во предупреждений перед баном
MOD_ROLE = "Moderator"  # Название роли модераторов
LOG_CHANNEL = "mod-logs" # Название канала для логов

# База данных (временная, для продакшена используйте SQLite/Postgres)
warnings = {}

@bot.event
async def on_ready():
    print(f'Бот {bot.user.name} готов к работе!')
    await bot.change_presence(activity=discord.Game(name="Защищаю сервер"))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # Автомодерация плохих слов
    banned_words = ["оскорбление", "запрещенное_слово", "спам"]
    if any(word in message.content.lower() for word in banned_words):
        await message.delete()
        warn_msg = await message.channel.send(
            f"{message.author.mention}, сообщение удалено! Нарушение правил."
        )
        await add_warning(message.author)
        await asyncio.sleep(5)
        await warn_msg.delete()
    
    await bot.process_commands(message)

async def add_warning(user):
    if user.id not in warnings:
        warnings[user.id] = 0
    warnings[user.id] += 1
    
    if warnings[user.id] >= WARN_LIMIT:
        # Автобан при превышении лимита
        await user.ban(reason="Автоматический бан за превышение предупреждений")
        await log_action(f"🚨 **БАН** | Пользователь {user} забанен автоматически")

@bot.command()
@commands.has_role(MOD_ROLE)
async def warn(ctx, member: discord.Member, *, reason="Не указана"):
    await add_warning(member)
    await ctx.send(f"⚠️ {member.mention} получил предупреждение. Причина: {reason}")
    await log_action(f"⚠️ **WARN** | {member} | Модератор: {ctx.author} | Причина: {reason}")

@bot.command()
@commands.has_role(MOD_ROLE)
async def ban(ctx, member: discord.Member, *, reason="Не указана"):
    await member.ban(reason=reason)
    await ctx.send(f"🚫 Пользователь {member} забанен. Причина: {reason}")
    await log_action(f"🚫 **BAN** | {member} | Модератор: {ctx.author} | Причина: {reason}")

@bot.command()
@commands.has_role(MOD_ROLE)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await log_action(f"🧹 **CLEAR** | {ctx.author} очистил {amount} сообщений в #{ctx.channel.name}")

async def log_action(message):
    channel = discord.utils.get(bot.get_all_channels(), name=LOG_CHANNEL)
    if channel:
        await channel.send(f"[{discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

# Запуск бота
TOKEN = "ВАШ_ТОКЕН_БОТА"  # Замените на реальный токен
bot.run(TOKEN)
