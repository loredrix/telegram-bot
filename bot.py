import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, ChatJoinRequest, CallbackQuery,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command


BOT_TOKEN = "8575624948:AAEbpWsoq1VAQbZ1qU7LOZd4fUlN5ix5VUo"
GROUP_ID = "1002148244160"
ADMIN_IDS = [1311250812]

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# --- Вопросы ---
questions = [
    ("Привет! Чтобы вступить в группу ответь на три простых вопроса! В каком поселке располагается микрорайон?",
     [("Кедровый", "1"), ("Засолочный", "2"),
      ("Раменский", "3"), ("Советский", "4"),
      ("Солонцы", "5")],
     "5"),

    ("Соглашаетесь ли Вы с правилами чата?",
     [("Да", "1"), ("Нет", "2")],
     "1"),

    ("В каком крае располагается микрорайон?",
     [("Краснодарский край", "1"),
      ("Алтайский край", "2"),
      ("Красноярский край", "3")],
     "3"),
]

user_sessions = {}

def make_keyboard(q_index: int) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=text, callback_data=f"{q_index}:{code}")]
        for text, code in questions[q_index][1]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.message(~F.chat.type.in_({"private"}))
async def ignore_non_private(_: Message):
    # ничего не делаем и НИЧЕГО не отвечаем
    return


@dp.message(Command("start"), F.chat.type == "private")
async def start_cmd(message: Message):
    await message.answer(
        "Привет! ✅ Я работаю.\n"
        "Чтобы вступить в чат, подай заявку в группу.\n"
        "Важно: сначала нажми Start у бота, затем подавай заявку."
    )


@dp.chat_join_request()
async def join_request(req: ChatJoinRequest):
    user_sessions[req.from_user.id] = {
        "chat_id": req.chat.id,
        "step": 0,
        "wrong": False,
    }

  
    try:
        await bot.send_message(
            req.from_user.id,
            questions[0][0],
            reply_markup=make_keyboard(0),
        )
    except Exception:
       
        for admin in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin,
                    f"⚠️ Пользователь подал заявку, но я не смог написать ему в личку.\n"
                    f"{req.from_user.full_name}\nID: {req.from_user.id}\n"
                    f"Пусть нажмёт Start у бота."
                )
            except Exception:
                pass

@dp.callback_query()
async def answer_handler(callback: CallbackQuery):
    
    if callback.message and callback.message.chat.type != "private":
        await callback.answer()
        return

    user_id = callback.from_user.id

    if user_id not in user_sessions:
        await callback.answer("Сессия не найдена. Подайте заявку заново.", show_alert=True)
        return

    q_index, code = callback.data.split(":")
    q_index = int(q_index)

    session = user_sessions[user_id]
    correct = questions[q_index][2]

    if code != correct:
        session["wrong"] = True

    session["step"] += 1

    if session["step"] < len(questions):
        next_q = session["step"]
        await callback.message.edit_text(
            questions[next_q][0],
            reply_markup=make_keyboard(next_q),
        )
        await callback.answer()
        return

    
    if not session["wrong"]:
        try:
            await bot.approve_chat_join_request(
                chat_id=session["chat_id"],
                user_id=user_id,
            )
            await callback.message.edit_text("✅ Проверка пройдена. Заявка одобрена, добро пожаловать!")
        except Exception:
            await callback.message.edit_text(
                "Я не смог автоматически одобрить заявку. Админы проверят вручную."
            )
            session["wrong"] = True  # уводим в модерацию

    if session["wrong"]:
        for admin in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin,
                    "❗ Ошибка в ответах у пользователя:\n"
                    f"{callback.from_user.full_name}\n"
                    f"ID: {user_id}"
                )
            except Exception:
                pass

        await callback.message.edit_text("⏳ Ответы отправлены админам на проверку.")

    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
