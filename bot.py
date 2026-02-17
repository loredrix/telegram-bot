import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import *
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

BOT_TOKEN = "8575624948:AAG16czSouo78azbEOp-Lg7_yfjKUm6eLsg"
GROUP_ID = "1002148244160"
ADMIN_IDS = "1311250812"

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

from aiogram.filters import Command

@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer(
        "Привет! ✅ Я работаю.\n"
        "Если ты подал заявку в группу — я пришлю вопросы и после них одобрю заявку."
    )

@dp.message()
async def show_group_id(message: Message):
    if message.chat.type in ("group", "supergroup"):
        await message.reply(f"ID этой группы: {message.chat.id}")
questions = [
    ("В каком поселке располагается микрорайон?",
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
     "3")
]

user_sessions = {}

def make_keyboard(q_index):
    buttons = [[InlineKeyboardButton(text=text, callback_data=f"{q_index}:{code}")]
               for text, code in questions[q_index][1]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.chat_join_request()
async def join_request(req: ChatJoinRequest):
    user_sessions[req.from_user.id] = {
        "chat_id": req.chat.id,
        "step": 0,
        "wrong": False
    }

    await bot.send_message(
        req.from_user.id,
        questions[0][0],
        reply_markup=make_keyboard(0)
    )

@dp.callback_query()
async def answer_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
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
            reply_markup=make_keyboard(next_q)
        )
    else:
        if not session["wrong"]:
            await bot.approve_chat_join_request(
                chat_id=session["chat_id"],
                user_id=user_id
            )
            await callback.message.edit_text("✅ Проверка пройдена. Добро пожаловать!")
        else:
            for admin in ADMIN_IDS:
                await bot.send_message(
                    admin,
                    f"❗ Ошибка в ответах у пользователя:\n"
                    f"{callback.from_user.full_name}\n"
                    f"ID: {user_id}"
                )
            await callback.message.edit_text(
                "⏳ Ответы отправлены админам на проверку."
            )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
