import logging
import contextlib
import os
import random
import re
import string
import time
import redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from random import shuffle
from captcha.image import ImageCaptcha
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.dispatcher.filters import CommandStart, CommandHelp
from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import TOKEN, ADMINS

logging.basicConfig(level=logging.INFO)

bot=Bot(token=TOKEN,parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())

class STATES(StatesGroup):
    cap = State()


REDIS ="localhost"
redis_client = redis.StrictRedis(host=REDIS, decode_responses=True, db=8)
image = ImageCaptcha()

PREDEFINED_STR = re.sub(r"[1l0oOI]", "", string.ascii_letters + string.digits)
IDLE_SECONDS = 5 * 60

def generate_char():
    return "".join([random.choice(PREDEFINED_STR) for _ in range(4)])

class Group(BoundFilter):
    async def check(self,message: types.Message):
        return message.chat.type == types.ChatType.SUPERGROUP or types.ChatType.GROUP or types.ChatType.SUPER_GROUP

@dp.message_handler(CommandStart())
async def MistrUz(message: types.Message):
    await message.reply(f"Salom {message.from_user.full_name}!\n"
                        f"Bot kodi sotiladi : @MrGayratov\n")


@dp.message_handler(chat_id=-1001825384988,content_types=['new_chat_members'])
async def bot_echo(message: types.Message):
    user_id = message.new_chat_members[0].id
    full_name = message.new_chat_members[0].full_name
    await message.chat.restrict(
            user_id,
            permissions=types.ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_invite_users=False,
                can_send_polls=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_pin_messages=False
            ))
    chars = generate_char()
    data = image.generate(chars)
    data.name = f"{message.from_user.id}-captcha.png"
    user_button = []
    for _ in range(4):
        fake_char = generate_char()
        button = types.InlineKeyboardButton(text=fake_char, callback_data=f"{fake_char}_{message.from_user.id}")
        user_button.append(button)
    button1 = types.InlineKeyboardButton(text=chars, callback_data=f"{chars}|{message.from_user.id}")
    user_button.append(button1)
    shuffle(user_button)
    markup = types.InlineKeyboardMarkup(row_width=5,inline_keyboard=[user_button])
    await message.reply_photo(data, caption=f"*Assalomu alaykum! 😊*\n 👤 [{full_name}](tg://user?id={user_id}) *guruhimizga xush kelibsiz!*\n"
                                                    f"*Guruhda yozish uchun rasimdagi natijani kiriting!*",
                                            reply_markup=markup, parse_mode=types.ParseMode.MARKDOWN
                                            )

@dp.callback_query_handler(lambda message: types.ChatType.SUPERGROUP or types.ChatType.GROUP or types.ChatType.SUPER_GROUP)
async def process_ozgarish(call: types.CallbackQuery, state: FSMContext):
    data = call.data
    data_user = call.data.split("|")
    data_user_ = call.data.split("_")
    middle_character = data[4:5]
    if middle_character == "|":
        if call.from_user.id == int(data_user[1]):
            await call.answer("Guruxda yozishingiz mumkin!")
            await call.message.delete()
            await call.message.chat.restrict(
                call.from_user.id,
                permissions=types.ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_invite_users=True,
                    can_send_polls=True,
                    can_add_web_page_previews=False,
                    can_change_info=False,
                    can_pin_messages=False
                ))
        else:
            await call.answer("Bu captcha siz uchunmas!", show_alert=True)
    elif middle_character != "|":
        if call.from_user.id == int(data_user_[1]):
            await call.answer("Notoʻgʻri natija kiritildi", show_alert=True)
        else:
            await call.answer("Bu captcha siz uchunmas !", show_alert=True)

async def on_startup_notifiy(dp:Dispatcher):
    for admin in ADMINS:
        try:
            await dp.bot.send_message(admin, "<b>Bot ishga tushdi...</b>")
        except:
            pass
async def on_startup(dispatcher):
    await on_startup_notifiy(dispatcher)


if __name__ =="__main__":
    executor.start_polling(dp, on_startup=on_startup,skip_updates=True)