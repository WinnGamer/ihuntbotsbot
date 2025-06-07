import re
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, BaseFilter
import os

API_TOKEN = '8185508139:AAE691do5tGaL4SQZr_MO2RF26mmtQXJjdU'
BLACKLIST_FILE = 'blacklist.txt'

def load_blacklist():
    if not os.path.exists(BLACKLIST_FILE):
        return []
    with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def save_blacklist(words):
    with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
        for word in words:
            f.write(word + '\n')

blacklist = load_blacklist()

def is_spam(text):
    text = text.lower()
    for pattern in blacklist:
        if re.search(pattern, text):
            return True
    return False

class SpamFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return is_spam(message.text or "")

async def anti_spam_handler(message: types.Message, bot: Bot):
    await message.delete()
    try:
        await bot.ban_chat_member(message.chat.id, message.from_user.id)
    except Exception as e:
        print(f"Ошибка при бане: {e}")

async def addword_handler(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Напиши: /addword слово")
        return
    word = args[1].strip()
    if word in blacklist:
        await message.reply("Уже в чёрном списке.")
    else:
        blacklist.append(word)
        save_blacklist(blacklist)
        await message.reply(f"Добавлено в чёрный список: {word}")

async def delword_handler(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Напиши: /delword слово")
        return
    word = args[1].strip()
    if word in blacklist:
        blacklist.remove(word)
        save_blacklist(blacklist)
        await message.reply(f"Удалено из чёрного списка: {word}")
    else:
        await message.reply("Такого слова нет в чёрном списке.")

async def banlist_handler(message: types.Message):
    if not blacklist:
        await message.reply("Чёрный список пуст.")
    else:
        await message.reply("Чёрный список:\n" + "\n".join(blacklist))

async def unban_handler(message: types.Message, bot: Bot):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].startswith('@'):
        await message.reply("Напиши: /unban @username")
        return
    username = args[1][1:].strip()
    # Сначала попробуем найти юзера по username среди участников/бывших участников
    try:
        # Получаем список участников (ограничение Telegram: можно только для супергрупп и не всегда полный)
        members = []
        async for member in bot.get_chat_administrators(message.chat.id):
            members.append(member)
        for member in members:
            user = member.user
            if user.username and user.username.lower() == username.lower():
                try:
                    await bot.unban_chat_member(message.chat.id, user.id)
                    await message.reply(f"Пользователь @{username} разбанен.")
                    return
                except Exception as e:
                    await message.reply(f"Ошибка при разбане: {e}")
                    return
        await message.reply(f"Пользователь @{username} не найден среди админов группы.\n"
                            f"Если он не админ, разбаньте вручную по user_id.")
    except Exception as e:
        await message.reply(f"Ошибка поиска пользователя: {e}")

async def start_handler(message: types.Message):
    await message.reply(
        "Я антиспам-бот!\n\n"
        "Доступные команды для админов:\n"
        "/addword слово — добавить в чёрный список\n"
        "/delword слово — удалить из чёрного списка\n"
        "/banlist — показать чёрный список\n"
        "/unban @username — разбанить пользователя по username\n"
        "\nДобавляй меня админом в группу и управляй списком спам-слов прямо в чате!"
    )

async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    dp.message.register(anti_spam_handler, SpamFilter())
    dp.message.register(addword_handler, Command("addword"))
    dp.message.register(delword_handler, Command("delword"))
    dp.message.register(banlist_handler, Command("banlist"))
    dp.message.register(unban_handler, Command("unban"))
    dp.message.register(start_handler, Command("start"))

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
