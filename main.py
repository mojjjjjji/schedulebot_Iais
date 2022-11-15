#Общая часть
from aiogram                            import types, Dispatcher, Bot               #тип данных телеграмма, диспетчер, бот
from aiogram.utils                      import executor                             #Запускает работу диспетчера
from aiogram.types                      import KeyboardButton, ReplyKeyboardMarkup  #Модуль для работы с клавиатурой
from aiogram.dispatcher                 import FSMContext                           #Класс используется для того чтобы в handler'e указать машинное состояние
from aiogram.dispatcher.filters.state   import State, StatesGroup                   #
from aiogram.contrib.fsm_storage.memory import MemoryStorage                        #Класс позволяет хранить данные в оперативной памяти 
from functions                          import *                                    #
from aiogram.dispatcher.filters         import Text
from datetime import datetime
from calendar import monthrange
import asyncio
import os       #Импортирует модуль os, чтобы мы могли прочитать наш TOKEN
import re       #Модуль рег. выражений
import pymysql  #Модуль управления БД

storage = MemoryStorage()
bot = Bot(token = '5605614034:AAHNoNXooC9AN-cXT2auLennD0qlfVFxsKY') #Токен бота
dp = Dispatcher(bot, storage=storage)                               #Передан экземпляр нашего бота

#Создание этапов для нового напоминания
class FSMCreateReminder(StatesGroup):
    description = State()   #Этап создания описания
    date_and_time = State() #Этап создания даты и время

#Создание этапов для нового напоминания
class FSMEditReminder(StatesGroup):
    choice = State()   #Этап выбора
    description = State()   #Этап изменения описания
    date_and_time = State() #Этап изменения даты и время

#Создание этапов для удаления напоминания
class FSMDeleteReminder(StatesGroup):
    choice = State()   #Этап удаления 


@dp.message_handler()                            #Означает событие, когда в наш чат кто-то что-то пишет
async def echo_message(message : types.Message): #Функция которая принимает смс от пользователя
    
    #Начать использование
    if re.fullmatch('/start', message.text):
        keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton('Создать напоминание')).add(KeyboardButton('Мои напоминания'))
        await bot.send_message(chat_id= message.from_user.id, text='Привет.\nБот создан чтобы напомнить вам о ваших запланированных делах, которые вы можете добавлять в свой список напоминаний.', reply_markup=keyboard)
    
    #Создать напоминание
    elif re.fullmatch('Создать напоминание', message.text):
        keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton('отмена'))
        await bot.send_message(message.from_user.id, 'Напишите о чем вам напомнить.', reply_markup=keyboard)
        #Создание состояния
        await FSMCreateReminder.description.set()
    
    #Мои напоминания
    elif re.fullmatch('Мои напоминания', message.text):
        keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton('Редактировать')).add(KeyboardButton('Удалить')).add(KeyboardButton('Меню')) 
        await bot.send_message(chat_id= message.from_user.id, text='Список ваших напоминаний:', reply_markup=keyboard) #Отправка сообщения пользователю
        #Подключение базы данных
        connection = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='qwert123',
            database='reminder_bot_bd',
            cursorclass=pymysql.cursors.DictCursor
        )    
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM reminder_bot_bd.info_table WHERE `user_id` = '{message.from_user.id}' ORDER BY `date` ASC, `time` ASC")
            bd = cursor.fetchall()
            ansMsg = ''
            for i in range(len(bd)):
                ansMsg += str(i+1) + '. ' + bd[i]['date'] + ' ' + bd[i]['description'] + ' в ' + bd[i]['time'] + '\n'
            await message.answer(ansMsg)
        connection.close()
    
    #Удалить напоминание
    elif re.fullmatch('Удалить', message.text):
        keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton('отмена'))
        await bot.send_message(message.from_user.id, 'Выберите напоминание по списку, которое хотите удалить.', reply_markup=keyboard)
        await FSMDeleteReminder.choice.set()
    
    #Редактировать напоминание
    elif re.fullmatch('Редактировать', message.text):
        keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton('отмена'))
        await bot.send_message(message.from_user.id, 'Выберите напоминание по списку, которое хотите редактировать.', reply_markup=keyboard)
        await FSMEditReminder.choice.set()   
    
    #Выход в главное меню
    elif re.fullmatch('Меню', message.text):
        keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton('Создать напоминание')).add(KeyboardButton('Мои напоминания'))
        await bot.send_message(message.from_user.id, 'Вы вернулись в главное меню', reply_markup=keyboard)
    
    # #Вывод несуществующих команд
    else:
        await message.answer('Возможно вы ввели неправильную команду.')
    
    
    #Выход из состояний
    @dp.message_handler(state="*", commands='отмена')
    @dp.message_handler(Text(equals='отмена', ignore_case = True), state="*")
    async def cancel_handler(message: types.Message, state):
        current_state = await state.get_state()
        if current_state is None:
            return
        keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton('Создать напоминание')).add(KeyboardButton('Мои напоминания'))
        await bot.send_message(message.from_user.id, 'Вы вернулись в главное меню', reply_markup=keyboard)
        await state.finish() 
    
    
    #Ловим первый ответ для создания напоминания 
    #Этап 1, создания описания
    @dp.message_handler(state=FSMCreateReminder.description)
    async def load_description(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data['description'] = message.text
        #Вызов формы для заполнения даты и времени напоминания    
        form = mode_inline_keyboard()
        await bot.send_message(message.from_user.id, 'Форма заполнения даты и времени', reply_markup=form)
        #Переход в след. машинное состояние FSMCreateReminder.date_and_time
        await FSMCreateReminder.next()

    #Этап 2, создания даты и время
    @dp.callback_query_handler(state=FSMCreateReminder.date_and_time)
    async def buttons(call: types.CallbackQuery, state: FSMContext):
        months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        #Изменение месяца
        if call.data.split('_')[1] == 'month':
            #Изменяем тект кнопки, какая кнопка, на какой строчке, текущая форма
            inlkb = mode_inline_keyboard(months[int(call.data.split('_')[0])], 'save_monthResult', 3, call['message']['reply_markup'])
            #Изменение клавиатуры. Id пользователя, Id сообщения, новая форма
            await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=inlkb)
        #Изменение года
        elif call.data.split('_')[1] == 'year':
            if call.data.split('_')[0] == 'plus':
                if int(call['message']['reply_markup']['inline_keyboard'][1][0]['text'])+1 <= datetime.today().year + 5:
                    inlkb = mode_inline_keyboard(str(int(call['message']['reply_markup']['inline_keyboard'][1][0]['text'])+1), 'save_yearResult', 1, call['message']['reply_markup'])
                    await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=inlkb)
                return
            if call.data.split('_')[0] == 'minus':
                if int(call['message']['reply_markup']['inline_keyboard'][1][0]['text'])-1 >= datetime.today().year:
                    inlkb = mode_inline_keyboard(str(int(call['message']['reply_markup']['inline_keyboard'][1][0]['text'])-1), 'save_yearResult', 1, call['message']['reply_markup'])
                    await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=inlkb)
                return
        #Изменение дня
        elif call.data.split('_')[1] == 'day':
            if call.data.split('_')[0] == 'plus':
                if int(call['message']['reply_markup']['inline_keyboard'][8][0]['text'])+1 <= monthrange(datetime.today().year, months.index(call['message']['reply_markup']['inline_keyboard'][3][0]['text'])+1)[1]:
                    inlkb = mode_inline_keyboard(str(int(call['message']['reply_markup']['inline_keyboard'][8][0]['text'])+1), 'save_dayResult', 8, call['message']['reply_markup'])
                    await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=inlkb)
                return
            if call.data.split('_')[0] == 'minus':
                if 1 <= int(call['message']['reply_markup']['inline_keyboard'][8][0]['text'])-1:    
                    inlkb = mode_inline_keyboard(str(int(call['message']['reply_markup']['inline_keyboard'][8][0]['text'])-1), 'save_dayResult', 8, call['message']['reply_markup'])
                    await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=inlkb)
                return
        #Изменение часа
        elif call.data.split('_')[1] == 'hour':
            if call.data.split('_')[0] == 'plus':
                if int(call['message']['reply_markup']['inline_keyboard'][10][0]['text'])+1 <= 23:
                    inlkb = mode_inline_keyboard(str(int(call['message']['reply_markup']['inline_keyboard'][10][0]['text'])+1), 'save_hourResult', 10, call['message']['reply_markup'])
                    await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=inlkb)
                return
            if call.data.split('_')[0] == 'minus':
                if int(call['message']['reply_markup']['inline_keyboard'][10][0]['text'])-1 >= 0:    
                    inlkb = mode_inline_keyboard(str(int(call['message']['reply_markup']['inline_keyboard'][10][0]['text'])-1), 'save_hourResult', 10, call['message']['reply_markup'])
                    await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=inlkb)
                return
        #Изменение минут
        elif call.data.split('_')[1] == 'minute':
            if call.data.split('_')[0] == 'plus':
                if int(call['message']['reply_markup']['inline_keyboard'][11][0]['text'])+1 <= 59:
                    inlkb = mode_inline_keyboard(str(int(call['message']['reply_markup']['inline_keyboard'][11][0]['text'])+1), 'save_minuteResult', 11, call['message']['reply_markup'])
                    await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=inlkb)
                return
            if call.data.split('_')[0] == 'minus':
                if int(call['message']['reply_markup']['inline_keyboard'][11][0]['text'])-1 >= 0:
                    inlkb = mode_inline_keyboard(str(int(call['message']['reply_markup']['inline_keyboard'][11][0]['text'])-1), 'save_minuteResult', 11, call['message']['reply_markup'])
                    await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=inlkb)
                return
        #Сохранение
        elif call.data == 'save_but':
            # Дата для БД
            months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
            day = call['message']['reply_markup']['inline_keyboard'][8][0]['text']
            month = str(months.index(call['message']['reply_markup']['inline_keyboard'][3][0]['text'])+1)
            if len(call['message']['reply_markup']['inline_keyboard'][8][0]['text']) == 1:
                day = '0' + call['message']['reply_markup']['inline_keyboard'][8][0]['text']
            if len(str(months.index(call['message']['reply_markup']['inline_keyboard'][3][0]['text']))) == 1:
                month = '0' + str(months.index(call['message']['reply_markup']['inline_keyboard'][3][0]['text'])+1)
            #Конец состояния и сохранение в БД
            async with state.proxy() as data:
                #Добавление даты
                data['date'] = day + '.' + month + '.' + call['message']['reply_markup']['inline_keyboard'][1][0]['text']
                #Добавление времени
                data['time'] = call['message']['reply_markup']['inline_keyboard'][10][0]['text'] + ':' + call['message']['reply_markup']['inline_keyboard'][11][0]['text']
                await message.answer('Ваше напоминание создано: ' + data['date'] + ', ' + data['description'] + ' в ' + data['time'] + '.')   
                #Сохранение напоминания в БД
                #Подключение БД
                connection = pymysql.connect(
                    host='localhost',
                    port=3306,
                    user='root',
                    password='qwert123',
                    database='reminder_bot_bd',
                    cursorclass=pymysql.cursors.DictCursor
                )
                #Запись в БД
                with connection.cursor() as cursor:
                    cursor.execute(f"INSERT INTO reminder_bot_bd.info_table VALUES ('{message.from_user.id}', '{data['date']}', '{data['time']}', '{data['description']}', 0)")
                    connection.commit()
                connection.close()
            keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton('Создать напоминание')).add(KeyboardButton('Мои напоминания'))
            await bot.send_message(chat_id= message.from_user.id, text='Главное меню', reply_markup=keyboard)
            #Закрыть состояние
            await state.finish()  
    
    
    #Ловим ответ на удаление
    @dp.message_handler(state=FSMDeleteReminder.choice)
    async def load_choice(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            if re.search('\D', message.text):
                await bot.send_message(chat_id= message.from_user.id, text='Вам необходимо ввести число')
            else:
                data['choice'] = message.text
                #Подключение базы данных
                connection = pymysql.connect(
                    host='localhost',
                    port=3306,
                    user='root',
                    password='qwert123',
                    database='reminder_bot_bd',
                    cursorclass=pymysql.cursors.DictCursor
                )    
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT * FROM reminder_bot_bd.info_table WHERE `user_id` = '{message.from_user.id}' ORDER BY `date` ASC, `time` ASC")
                    bd = cursor.fetchall()   
                    if int(data['choice'])-1 < len(bd) and int(data['choice'])-1 >= 0:
                        cursor.execute(f"DELETE FROM reminder_bot_bd.info_table WHERE  `id_reminder` = {bd[int(data['choice'])-1]['id_reminder']}")
                        connection.commit()
                        keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton('Создать напоминание')).add(KeyboardButton('Мои напоминания'))
                        await bot.send_message(chat_id= message.from_user.id, text='Это напоминание успешно удалено', reply_markup=keyboard)
                        ansMsg = 'Ваш новый список напоминаний: \n'
                        bd.remove(bd[int(data['choice'])-1])
                        for i in range(len(bd)):
                            ansMsg += str(i+1) + '. ' + bd[i]['date'] + ' ' + bd[i]['description'] + ' в ' + bd[i]['time'] + '\n'
                        await message.answer(ansMsg)
                        #Закрыть состояние
                        await state.finish() 
                    else:
                        await message.answer('К сожалению такого напоминания нет в списке, попробуйте еще раз.')
                        await state.finish()
                        await FSMDeleteReminder.choice.set()
                connection.close()


    #Ловим 1 ответ на редактирование
    @dp.message_handler(state=FSMEditReminder.choice)
    async def load_choice(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            if re.search('\D', message.text):
                await bot.send_message(chat_id= message.from_user.id, text='Вам необходимо ввести число')
            else:
                data['choice'] = message.text
                #Подключение базы данных
                connection = pymysql.connect(
                    host='localhost',
                    port=3306,
                    user='root',
                    password='qwert123',
                    database='reminder_bot_bd',
                    cursorclass=pymysql.cursors.DictCursor
                )    
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT * FROM reminder_bot_bd.info_table WHERE `user_id` = '{message.from_user.id}' ORDER BY `date` ASC, `time` ASC")
                    bd = cursor.fetchall()

                    if int(data['choice'])-1 < len(bd) and int(data['choice'])-1 >= 0:
                        year = bd[int(data['choice'])-1]['date'].split('.')[2]
                        if list(bd[int(data['choice'])-1]['date'].split('.')[1])[0] != '0': 
                            months = bd[int(data['choice'])-1]['date'].split('.')[1]
                        else:
                            months = list(bd[int(data['choice'])-1]['date'].split('.')[1])[1]
                        if list(bd[int(data['choice'])-1]['date'].split('.')[0])[0] != '0': 
                            day = bd[int(data['choice'])-1]['date'].split('.')[0]
                        else:
                            day = list(bd[int(data['choice'])-1]['date'].split('.')[0])[1]
                        hours = bd[int(data['choice'])-1]['time'].split(':')[0]
                        minute = bd[int(data['choice'])-1]['time'].split(':')[1]
                        
                        data['id_reminder'] = bd[int(data['choice'])-1]['id_reminder']
                        data['year'] = year
                        data['months'] = months
                        data['day'] = day
                        data['hours'] = hours
                        data['minute'] = minute
                        #След. состояние
                        await message.answer('Редактирование описания')
                        await FSMEditReminder.next() 
                    else:
                        await message.answer('К сожалению такого напоминания нет в списке, попробуйте еще раз.')
                        await state.finish()
                        await FSMEditReminder.choice.set()  
    
    
    #Ловим 2 ответ на редактирование
    @dp.message_handler(state=FSMEditReminder.description)
    async def load_new_description(message: types.Message, state: FSMContext): #, call: types.CallbackQuery
        async with state.proxy() as data:
            data['description'] = message.text
        #Создание формы
        months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        form = mode_inline_keyboard()
        form = mode_inline_keyboard(months[int(data['months'])-1], 'save_monthResult', 3, form)
        form = mode_inline_keyboard(str(int(data['year'])), 'save_yearResult', 1, form)
        form = mode_inline_keyboard(str(int(data['day'])), 'save_dayResult', 8, form)
        form = mode_inline_keyboard(str(data['hours']), 'save_hourResult', 10, form)
        form = mode_inline_keyboard(str(int(data['minute'])), 'save_minuteResult', 11, form)
        await bot.send_message(message.from_user.id, 'Форма редактирования даты и времени', reply_markup=form)

        #След. состояние
        await FSMEditReminder.next()  
    
    
    #Ловим 3 ответ на редактирование
    @dp.callback_query_handler(state=FSMEditReminder.date_and_time)
    async def buttons(call: types.CallbackQuery, state: FSMContext):
        months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        #Изменение месяца
        if call.data.split('_')[1] == 'month':
            #Изменяем тект кнопки, какая кнопка, на какой строчке, текущая форма
            inlkb = mode_inline_keyboard(months[int(call.data.split('_')[0])], 'save_monthResult', 3, call['message']['reply_markup'])
            #Изменение клавиатуры. Id пользователя, Id сообщения, новая форма
            await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=inlkb)
        #Изменение года
        elif call.data.split('_')[1] == 'year':
            if call.data.split('_')[0] == 'plus':
                if int(call['message']['reply_markup']['inline_keyboard'][1][0]['text'])+1 <= datetime.today().year + 5:
                    inlkb = mode_inline_keyboard(str(int(call['message']['reply_markup']['inline_keyboard'][1][0]['text'])+1), 'save_yearResult', 1, call['message']['reply_markup'])
                    await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=inlkb)
                return
            if call.data.split('_')[0] == 'minus':
                if int(call['message']['reply_markup']['inline_keyboard'][1][0]['text'])-1 >= datetime.today().year:
                    inlkb = mode_inline_keyboard(str(int(call['message']['reply_markup']['inline_keyboard'][1][0]['text'])-1), 'save_yearResult', 1, call['message']['reply_markup'])
                    await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=inlkb)
                return
        #Изменение дня
        elif call.data.split('_')[1] == 'day':
            if call.data.split('_')[0] == 'plus':
                if int(call['message']['reply_markup']['inline_keyboard'][8][0]['text'])+1 <= monthrange(datetime.today().year, months.index(call['message']['reply_markup']['inline_keyboard'][3][0]['text'])+1)[1]:
                    inlkb = mode_inline_keyboard(str(int(call['message']['reply_markup']['inline_keyboard'][8][0]['text'])+1), 'save_dayResult', 8, call['message']['reply_markup'])
                    await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=inlkb)
                return
            if call.data.split('_')[0] == 'minus':
                if 1 <= int(call['message']['reply_markup']['inline_keyboard'][8][0]['text'])-1:    
                    inlkb = mode_inline_keyboard(str(int(call['message']['reply_markup']['inline_keyboard'][8][0]['text'])-1), 'save_dayResult', 8, call['message']['reply_markup'])
                    await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=inlkb)
                return
        #Изменение часа
        elif call.data.split('_')[1] == 'hour':
            if call.data.split('_')[0] == 'plus':
                if int(call['message']['reply_markup']['inline_keyboard'][10][0]['text'])+1 <= 23:
                    inlkb = mode_inline_keyboard(str(int(call['message']['reply_markup']['inline_keyboard'][10][0]['text'])+1), 'save_hourResult', 10, call['message']['reply_markup'])
                    await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=inlkb)
                return
            if call.data.split('_')[0] == 'minus':
                if int(call['message']['reply_markup']['inline_keyboard'][10][0]['text'])-1 >= 0:    
                    inlkb = mode_inline_keyboard(str(int(call['message']['reply_markup']['inline_keyboard'][10][0]['text'])-1), 'save_hourResult', 10, call['message']['reply_markup'])
                    await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=inlkb)
                return
        #Изменение минут
        elif call.data.split('_')[1] == 'minute':
            if call.data.split('_')[0] == 'plus':
                if int(call['message']['reply_markup']['inline_keyboard'][11][0]['text'])+1 <= 59:
                    inlkb = mode_inline_keyboard(str(int(call['message']['reply_markup']['inline_keyboard'][11][0]['text'])+1), 'save_minuteResult', 11, call['message']['reply_markup'])
                    await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=inlkb)
                return
            if call.data.split('_')[0] == 'minus':
                if int(call['message']['reply_markup']['inline_keyboard'][11][0]['text'])-1 >= 0:
                    inlkb = mode_inline_keyboard(str(int(call['message']['reply_markup']['inline_keyboard'][11][0]['text'])-1), 'save_minuteResult', 11, call['message']['reply_markup'])
                    await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=inlkb)
                return
        #Сохранение
        elif call.data == 'save_but':
            # Дата для БД
            months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
            day = call['message']['reply_markup']['inline_keyboard'][8][0]['text']
            month = str(months.index(call['message']['reply_markup']['inline_keyboard'][3][0]['text'])+1)
            if len(call['message']['reply_markup']['inline_keyboard'][8][0]['text']) == 1:
                day = '0' + call['message']['reply_markup']['inline_keyboard'][8][0]['text']
            if len(str(months.index(call['message']['reply_markup']['inline_keyboard'][3][0]['text']))) == 1:
                month = '0' + str(months.index(call['message']['reply_markup']['inline_keyboard'][3][0]['text'])+1)
            #Конец состояния и сохранение в БД
            async with state.proxy() as data:
                #Добавление даты
                data['date'] = day + '.' + month + '.' + call['message']['reply_markup']['inline_keyboard'][1][0]['text']
                #Добавление времени
                data['time'] = call['message']['reply_markup']['inline_keyboard'][10][0]['text'] + ':' + call['message']['reply_markup']['inline_keyboard'][11][0]['text']
                await message.answer('Ваше напоминание изменено: ' + data['date'] + ', ' + data['description'] + ' в ' + data['time'] + '.')   
                #Сохранение напоминания в БД
                #Подключение БД
                connection = pymysql.connect(
                    host='localhost',
                    port=3306,
                    user='root',
                    password='qwert123',
                    database='reminder_bot_bd',
                    cursorclass=pymysql.cursors.DictCursor
                )
                #Запись в БД
                with connection.cursor() as cursor:
                    cursor.execute(f"UPDATE reminder_bot_bd.info_table SET `date` = '{data['date']}', `time` = '{data['time']}', `description` = '{data['description']}' WHERE `id_reminder` = {data['id_reminder']}")
                    connection.commit()
                connection.close()
            keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton('Создать напоминание')).add(KeyboardButton('Мои напоминания'))
            await bot.send_message(chat_id= message.from_user.id, text='Главное меню', reply_markup=keyboard)
            #Закрыть состояние
            await state.finish()


async def checker_reminer():
    while True:

        #Подключение базы данных
        connection = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='qwert123',
            database='reminder_bot_bd',
            cursorclass=pymysql.cursors.DictCursor
        )    
        with connection.cursor() as cursor:
            #Дата
            date_today = str(datetime.now().date()).split('-')[-1] + '.' + str(datetime.now().date()).split('-')[1] + '.' + str(datetime.now().date()).split('-')[0]
            #Время
            hour = str(datetime.now().hour)
            if len(hour) == 1:
                hour = '0' + hour
            minute = str(datetime.now().minute)
            if len(minute) == 1:
                minute = '0' + minute
            time_now = hour + ':' + minute

            cursor.execute(f"SELECT * FROM reminder_bot_bd.info_table WHERE `date` <= '{date_today}' AND `time` <= '{time_now}'") 
            bd = cursor.fetchall()
            if len(bd):
                for i in range(len(bd)):
                    await bot.send_message(bd[i]['user_id'], f"❗️Напоминание❗️\n\n{bd[i]['description']}")
                    cursor.execute(f"DELETE FROM reminder_bot_bd.info_table WHERE  `id_reminder` = {bd[i]['id_reminder']}")
                    connection.commit()
            
        connection.close()
        #Таймер 
        await asyncio.sleep(20)

 
if __name__ == '__main__':

    #Запуск асинх. функции для оповещения пользователей
    asyncio.get_event_loop().create_task(checker_reminer())
    
    #Запуск бота
    executor.start_polling(dp, skip_updates = True)