import asyncio
import re
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.client.default import DefaultBotProperties

from data import db

TOKEN = "8114460368:AAGxYdqomBzMfS-VgS3_bJHsaHK1srssoe8"
ADMINS = {764515145}  # Бастапқы админдер

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

class SendState(StatesGroup):
    waiting_for_text = State()

@router.message()
async def message_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "None"

    # /start
    if message.text == "/start":
        await db.add_user(user_id, username)
        await message.answer("Бага связь! Кош келдіңіз! Астына сообщение жазыңыз!")
        return

    # /admin
    if message.text == "/admin" and user_id in ADMINS:
        await message.answer(
            "📋 Админ панель:\n"
            "1. /send - Рассылка\n"
            "2. /users - Қолданушылар саны\n"
            "3. /addadmin @username - Админ қосу"
        )
        return

    # /users
    if message.text == "/users" and user_id in ADMINS:
        count = await db.count_users()
        await message.answer(f"📋 Жалпы қолданушылар саны: {count}")
        return

    # /addadmin @username
    if message.text.startswith("/addadmin") and user_id in ADMINS:
        try:
            username_arg = message.text.split("@")[1].strip()
            new_admin_id = await db.get_user_id_by_username(username_arg)
            if new_admin_id:
                ADMINS.add(new_admin_id)
                await message.answer(f"✅ @{username_arg} админ ретінде қосылды!")
                await bot.send_message(new_admin_id, "🎉 Сізге админ құқық берілді!")
            else:
                await message.answer("❌ Бұл адам ботты пайдаланбаған.")
        except:
            await message.answer("❌ Қате! Формат: /addadmin @username")
        return

    # /send
    if message.text == "/send" and user_id in ADMINS:
        await state.set_state(SendState.waiting_for_text)
        await message.answer("✍️ Рассылка мәтінін жазыңыз:")
        return

    # Admin reply
    if user_id in ADMINS and message.reply_to_message:
        try:
            reply_text = message.reply_to_message.text
            match = re.search(r"ID:\s*([0-9]+)", reply_text)
            if not match:
                await message.answer("❌ ID табылмады.")
                return
            reply_user_id = int(match.group(1))

            user_msg_line = [line for line in reply_text.split('\n') if "✉️:" in line]
            user_msg = user_msg_line[0].replace("✉️:", "").strip() if user_msg_line else "(жоқ)"

            await bot.send_message(
                reply_user_id,
                f"📬 <b>Ответ от админа:</b>\n"
                f"<b>Сіздің сұрағыңыз:</b> {user_msg}\n"
                f"<b>Жауап:</b> {message.text}\n\n"
                f"🗺️ Спавните для ответа!"
            )
            await message.answer("✅ Жауап жіберілді.")
        except Exception as e:
            await message.answer(f"❌ Қолданушыға жібере алмадым.\n\nҚате: {e}")
        return

    # Admin рассылка мәтіні
    if await state.get_state() == SendState.waiting_for_text.state and user_id in ADMINS:
        await state.clear()
        text = message.text
        users = await db.get_all_users()
        success, fail = 0, 0
        for user_id in users:
            try:
                await bot.send_message(user_id, f" Реклама от админа\n{text}")
                success += 1
                await asyncio.sleep(0.1)
            except:
                fail += 1
        await message.answer(f"✅ Жіберілді: {success} 🟥 Қате: {fail}")
        return

    # Қолданушы хабарламасы (админ емес)
    if user_id not in ADMINS:
        await db.add_user(user_id, username)
        await message.answer("⏳ Подождите, отвечаю недолго время!")

        forward_text = (
            f"🖑 Жаңа хабарлама!\n"
            f"👤 От: @{username}\n"
            f"🔖 ID: {user_id}\n"
            f"✉️: {message.text}\n"
            f"\n🗺️ Спавните для ответа!"
        )
        for admin_id in ADMINS:
            await bot.send_message(admin_id, forward_text)


async def main():
    await db.setup()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
