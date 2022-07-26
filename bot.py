from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.utils.markdown import text
from aiogram.types.message import ContentType
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton

import start_model

TOKEN = "U_TOKEN_HERE"
users = {}
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

start_kb = InlineKeyboardMarkup()
start_kb.add(InlineKeyboardButton('Перенести стиль',
                                    callback_data='go'))
start_kb.add(InlineKeyboardButton('Как это происходит?',
                                    callback_data='inf'))

style_kb = InlineKeyboardMarkup()
style_kb.add(InlineKeyboardButton('Перенести свой стиль',
                                    callback_data='user_style'))
style_kb.add(InlineKeyboardButton('Стилизуем под кислотного ктулху',
                                    callback_data='ktulh'))
style_kb.add(InlineKeyboardButton('Голубая мечта',
                                    callback_data='blue'))
style_kb.add(InlineKeyboardButton('Делаем огонь',
                                    callback_data='fire'))

@dp.message_handler(commands=['start'])
async def process_help_command(message: types.Message):
    await bot.send_message(message.chat.id, "Привет, я учебный проект для курса DLS. \nМожешь потестировать меня или узнать о том, как я работаю.", reply_markup= start_kb)

@dp.callback_query_handler(lambda c: c.data == 'inf')
async def process_help_command(call: types.CallbackQuery):
    await bot.answer_callback_query(call.id)
    message_text = text('Данный бот создан в учебных целях для курса DLS',
                        '\n\n Принцип передачи стиля заключается в определении двух функций расстояния.',
                        'Одна из них описывает, насколько друг от друга отличаются содержания двух изображений (Loss content). ',
                        'Вторая функция описывает разницу между двумя стилями изображений (Loss style).',
                        '\n\nСеть пытается преобразовать входное изображение так, чтобы минимизировать его расстояние Loss content с изображением контента ',
                        'и расстояние Loss 90style с изображением стиля.')
    await call.message.answer(message_text, reply_markup=start_kb)

#Меню переноса стилей
@dp.callback_query_handler(lambda c: c.data == 'go')
async def process_start_command(call: types.CallbackQuery):
    await bot.answer_callback_query(call.id)
    message_text = text('Данный алгоритм работает нагляднее, если переносить стиль с ярких, абстрактных картинок.',
                        '\n\nТы можешь загрузить свои картинки для трансфера стиля или воспользоваться предзагруженными вариантами',
                        '\n\nВыбор за тобой!')
    await call.message.answer(message_text, reply_markup= style_kb)

#Обработка с пользовательским стилем
@dp.callback_query_handler(lambda c: c.data == 'user_style')
async def start_own_style(call: types.CallbackQuery):
    await bot.answer_callback_query(call.id)
    await call.message.answer('Пришли картинку, стиль которой хочешь изменить')

    users[call.message.chat.id] = {'started': True, 'content': False, 'style': False, 'type': 1}

#Обработка изображений с сохраненным стилем
@dp.callback_query_handler(lambda c: c.data == 'ktulh')
async def start_own_style(call: types.CallbackQuery):
    await bot.answer_callback_query(call.id)
    await call.message.answer('Пришли картинку, стиль которой хочешь изменить')

    users[call.message.chat.id] = {'started': True, 'content': False, 'style': False, 'type': 2}

@dp.callback_query_handler(lambda c: c.data == 'blue')
async def start_own_style(call: types.CallbackQuery):
    await bot.answer_callback_query(call.id)
    await call.message.answer('Пришли картинку, стиль которой хочешь изменить')

    users[call.message.chat.id] = {'started': True, 'content': False, 'style': False, 'type': 3}

@dp.callback_query_handler(lambda c: c.data == 'fire')
async def start_own_style(call: types.CallbackQuery):
    await bot.answer_callback_query(call.id)
    await call.message.answer('Пришли картинку, стиль которой хочешь изменить')

    users[call.message.chat.id] = {'started': True, 'content': False, 'style': False, 'type': 4}

@dp.message_handler(content_types=['photo', 'document'])
async def get_images(message):
    if message.chat.id in users and users[message.chat.id]['type'] == 1:
        if not users[message.chat.id]['content']:
            users[message.chat.id]['content'] = True
            await message.photo[-1].download('content.jpg')
            await bot.send_message(message.chat.id, 'Теперь пришли картинку, стиль которой хочешь перенести на первую картинку')
        elif not users[message.chat.id]['style']:
            users[message.chat.id]['style'] = True
            await message.photo[-1].download('style.jpg')
            await bot.send_message(message.chat.id, 'Изображение будет обрабатываться около 20 мин, можешь сходить за чаем')
            await start_model.style_start()
            await bot.send_photo(message.from_user.id, open('result.jpg', 'rb'))
            users[message.chat.id] = {'started': False, 'content': False, 'style': False}
            await bot.send_message(message.chat.id, "Попробуешь еще?", reply_markup=start_kb)
    else:
        users[message.chat.id]['content'] = True
        await message.photo[-1].download('content.jpg')

        if users[message.chat.id]['type'] == 2:
            style = "images/ktulh.jpg"
        elif users[message.chat.id]['type'] == 3:
            style = "images/blue.jpg"
        elif users[message.chat.id]['type'] == 4:
            style = "images/fire.jpg"

        await bot.send_message(message.chat.id, 'Изображение будет обрабатываться около 20 мин, можешь сходить за чаем')
        await start_model.style_start(style)
        await bot.send_photo(message.from_user.id, open('result.jpg', 'rb'))
        users[message.chat.id] = {'started': False, 'content': False, 'style': False}
        await bot.send_message(message.chat.id, "Попробуешь еще?", reply_markup=start_kb)


@dp.message_handler(content_types=ContentType.ANY)
async def unknown_message(message: types.Message):
    message_text = text('Я не знаю, что с этим делать',
                        '\nЯ просто напомню, что есть команда ',
                        '/help')
    await bot.send_message(message.chat.id, message_text, reply_markup=start_kb)

if __name__ == '__main__':
    executor.start_polling(dp)
