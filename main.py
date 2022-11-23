#Общая часть
from aiogram                            import types, Dispatcher, Bot               #тип данных телеграмма, диспетчер, бот
from aiogram.utils                      import executor                             #Запускает работу диспетчера
from aiogram.types                      import KeyboardButton, ReplyKeyboardMarkup  #Модуль для работы с клавиатурой
from aiogram.dispatcher                 import FSMContext                           #Класс используется для того чтобы в handler'e указать машинное состояние
from aiogram.dispatcher.filters.state   import State, StatesGroup                   #
from aiogram.contrib.fsm_storage.memory import MemoryStorage                        #Класс позволяет хранить данные в оперативной памяти 
from functions                          import *                                    #
from aiogram.dispatcher.filters         import Text
from datetime import datetime, date
import asyncio
import os       #Импортирует модуль os, чтобы мы могли прочитать наш TOKEN
import re       #Модуль рег. выражений
import pymysql  #Модуль управления БД

storage = MemoryStorage()
bot = Bot(token = '5605614034:AAHNoNXooC9AN-cXT2auLennD0qlfVFxsKY') #Токен бота
dp = Dispatcher(bot, storage=storage)                               #Передан экземпляр нашего бота


#Этапы для создания напоминаний
class FSMCreateReminder(StatesGroup):
    description = State()   #Этап создания описания
    date = State() #Этап создания даты
    time = State() #Этап создания времени


# #Этапы для редактирования напоминаний
class FSMEditReminder(StatesGroup):
    description = State()   #Этап создания описания
    date = State() #Этап создания даты
    time = State() #Этап создания времени



#Начать использование
@dp.message_handler(commands=['start'])
async def cancel_handler(message: types.Message, state):
    keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton('Создать напоминание')).add(KeyboardButton('Мои напоминания'))
    await bot.send_message(chat_id= message.from_user.id, text='Привет.👋 \nБот создан чтобы напомнить вам о ваших запланированных делах, которые вы можете добавлять в свой список напоминаний. \nИспользуйте клавиатуру теллеграмма, чтобы...', reply_markup=keyboard)   



#Выход из состояний
@dp.message_handler(state="*", commands='🔙Отмена')
@dp.message_handler(Text(equals='🔙Отмена', ignore_case = True), state="*")
async def cancel_handler(message: types.Message, state):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer('Возможно вы ввели неправильную команду.')
        return  
    keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton('Создать напоминание')).add(KeyboardButton('Мои напоминания'))
    await bot.send_message(message.from_user.id, 'Вы вернулись в главное меню', reply_markup=keyboard)
    await state.finish()



#Создать напоминание
@dp.message_handler(text='Создать напоминание')
async def cancel_handler(message: types.Message, state):
    keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton('🔙Отмена'))
    await bot.send_message(message.from_user.id, '📃Напишите о чем вам напомнить.', reply_markup=keyboard)
    #Создание состояния
    await FSMCreateReminder.description.set()



#Ловим первый ответ для создания напоминания 
#Этап 1, создание описания
@dp.message_handler(state=FSMCreateReminder.description)
async def load_description(message: types.Message, state: FSMContext):
    if len(message.text) <= 100:
        await bot.send_message(message.from_user.id, '📅Напишите дату. \nФормат даты должен быть (дд.мм.гггг).')
        async with state.proxy() as data:
            data['description'] = message.text
        #Переход в след. этап состояния
        await FSMCreateReminder.next()
    else:
        await bot.send_message(chat_id= message.from_user.id, text='😐Размер сообщения не может превышать более 100 символов.\nПопробуйте еще раз')



#Этап 2, создание даты
@dp.message_handler(state=FSMCreateReminder.date)
async def buttons(message: types.Message, state: FSMContext):
    if len(message.text) == 10:
        async with state.proxy() as data:
            correctDate = False
            try:
                y = int(message.text.split('.')[2])
                m = int(message.text.split('.')[1])
                d = int(message.text.split('.')[0])
                correct_date = f'{y}-{m}-{d}'
                date(y, m, d)
                nowDate = datetime.now()
                
                if (y == nowDate.year and m == nowDate.month and d >= nowDate.day) or (y > nowDate.year) or  (y == nowDate.year and m > nowDate.month):
                    correctDate = True
                else:
                    correctDate = False
            except:
                correctDate = False
            if correctDate:
                data['date'] = correct_date
                await bot.send_message(message.from_user.id, '⏱Напишите время. \nФормат времени должен быть (чч:мм).')
                await FSMCreateReminder.next()
            else:
                await bot.send_message(chat_id= message.from_user.id, text='😐Вы ввели неправильную дату. \nПопробуйте еще раз. Дата должна быть в будущем времени. \nФормат написания даты (дд.мм.гггг).')
    else:
        await bot.send_message(chat_id= message.from_user.id, text='😐Размер сообщения должен быть 10 символов.\nФормат написания даты (дд.мм.гггг).\nПопробуйте еще раз.')

     

#Этап 3, создание времени
@dp.message_handler(state=FSMCreateReminder.time)
async def buttons(message: types.Message, state: FSMContext):
    if len(message.text) == 5:
        async with state.proxy() as data:
            try:
                hour = message.text.split(':')[0]
                min = message.text.split(':')[1]
                y = int(data['date'].split('-')[0])
                m = int(data['date'].split('-')[1])
                d = int(data['date'].split('-')[2])
                nowDate = datetime.now()
                data['time'] = message.text
                if int(hour) <= 23 and int(min) <= 59:
                    if nowDate.year == y and nowDate.month == m and nowDate.day == d:    
                        if nowDate.hour < int(hour) or (nowDate.hour == int(hour) and nowDate.minute < int(min)):
                            #Подключение БД
                            connection = pymysql.connect(
                                host='localhost',
                                port=3306,
                                user='root',
                                password='qwert123',
                                database='reminder_bot',
                                cursorclass=pymysql.cursors.DictCursor
                            )
                                #Запись в БД
                            with connection.cursor() as cursor:
                                cursor.execute(f"INSERT INTO reminder_bot.info_table VALUES ('{message.from_user.id}', '{data['date']}', '{data['time']}', '{data['description']}', 0)")
                                connection.commit()
                            connection.close()
                            keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton('Создать напоминание')).add(KeyboardButton('Мои напоминания'))
                            await bot.send_message(chat_id= message.from_user.id, text='Ваше напоминание успешно создано. \nГлавное меню.', reply_markup=keyboard)
                            #Закрыть состояние
                            await state.finish()
                        else:
                            await bot.send_message(chat_id= message.from_user.id, text='😐Вы ввели неправильное время. \nПопробуйте еще раз. Время должно быть в будущем. \nФормат написания времени (чч:мм)')
                    else:
                        #Подключение БД
                            connection = pymysql.connect(
                                host='localhost',
                                port=3306,
                                user='root',
                                password='qwert123',
                                database='reminder_bot',
                                cursorclass=pymysql.cursors.DictCursor
                            )
                                #Запись в БД
                            with connection.cursor() as cursor:
                                cursor.execute(f"INSERT INTO reminder_bot.info_table VALUES ('{message.from_user.id}', '{data['date']}', '{data['time']}', '{data['description']}', 0)")
                                connection.commit()
                            connection.close()
                            keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton('Создать напоминание')).add(KeyboardButton('Мои напоминания'))
                            await bot.send_message(chat_id= message.from_user.id, text='Ваше напоминание успешно создано. \nГлавное меню.', reply_markup=keyboard)
                            #Закрыть состояние
                            await state.finish()
                else:
                    await bot.send_message(chat_id= message.from_user.id, text='😐Вы ввели неправильное время. \nПопробуйте еще раз. Время должно быть в будущем. \nФормат написания времени (чч:мм)')
            except:
                await bot.send_message(chat_id= message.from_user.id, text='😐Вы ввели неправильное время. \nПопробуйте еще раз. Время должно быть в будущем. \nФормат написания времени (чч:мм)')
    else:
        await bot.send_message(chat_id= message.from_user.id, text='😐Размер сообщения должен быть 5 символов.\nФормат написания времени (чч:мм).\nПопробуйте еще раз.')



#Мои напоминания
@dp.message_handler(text='Мои напоминания')
async def cancel_handler(message: types.Message, state):
    #Подключение базы данных
    connection = pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        password='qwert123',
        database='reminder_bot',
        cursorclass=pymysql.cursors.DictCursor
    )    
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM reminder_bot.info_table WHERE `user_id` = '{message.from_user.id}' ORDER BY `date` ASC, `time` ASC")
        bd = cursor.fetchall()
        if not bd: #bd is None
            await bot.send_message(chat_id= message.from_user.id, text='😐У вас нет напоминаний.')
        else:
            ansMsg = '📄Список напоминаний:\n\n'
            id_reminder=[]
            for i in range(len(bd)):
                id_reminder.append(bd[i]['id_reminder'])
                ansMsg += str(i+1) + '. ' + bd[i]['description'] + ' (' + str(bd[i]['date']) + ' ' +  ' в ' + bd[i]['time'] + ')' + '\n'
            ansMsg += '\n'
            ansMsg += 'Выберите номер для редактирования:👇'
            async with state.proxy() as data:
                data['allRecord'] = len(bd)
            #Вызов формы для редактирования
            form = inline_keyboard_for_delete('start', len(bd), ' ', id_reminder)
            await bot.send_message(message.from_user.id, ansMsg, reply_markup=form)    
    connection.close()
         


#При нажатии на кнопки вызывается этот handler
@dp.callback_query_handler()
async def buttons(call: types.CallbackQuery, state: FSMContext):
    #Проверяем, на какую кнопку мы нажали
    #Кнопка выбора номера из списка напоминий 
    if call.data.split('_')[1] == 'number':
        #Подключение базы данных
        connection = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='qwert123',
            database='reminder_bot',
            cursorclass=pymysql.cursors.DictCursor
        )    
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM reminder_bot.info_table WHERE  `id_reminder` = {call.data.split('_')[0]}")
            bd = cursor.fetchall()
            async with state.proxy() as data:
                data['id_reminder'] = call.data.split('_')[0]
                data['oldDescription'] = bd[0]['description']
                data['oldDate'] = bd[0]['date']
                data['oldTime'] = bd[0]['time']
                data['message_id'] = call.message.message_id
            ansMsg = f'Напоминание                                               \n\n📃Описание: ' + bd[0]['description'] + '\n\n📅Дата: ' + str(bd[0]['date']) + '\n\n⏱Время: ' + bd[0]['time'] + '\n\nВыберите действие👇'
            #Изменение текста в сообщении
            await bot.edit_message_text(chat_id=call.from_user.id,message_id=call.message.message_id, text=ansMsg)
        connection.close()
        inlkb = inline_keyboard_for_delete('number', ' ', call.data.split('_')[0])
        #Изменение клавиатуры. Id пользователя, Id сообщения, новая форма
        await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=inlkb)   
    #Кнопка редактирования
    elif call.data.split('_')[1] == 'edit':
        inlkb = inline_keyboard_for_delete('edit', ' ', call.data.split('_')[0])
        #Изменение клавиатуры. Id пользователя, Id сообщения, новая форма
        await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=inlkb)
    #Кнопка удаления
    elif call.data.split('_')[1] == 'delete':
        #Подключение базы данных
        connection = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='qwert123',
            database='reminder_bot',
            cursorclass=pymysql.cursors.DictCursor
        )    
        with connection.cursor() as cursor:
            #Запрос на удаление  
            cursor.execute(f"DELETE FROM reminder_bot.info_table WHERE  `id_reminder` = {call.data.split('_')[0]}")
            #Сохранение запроса в БД
            connection.commit()
            keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton('Создать напоминание')).add(KeyboardButton('Мои напоминания'))
            # await bot.send_message(chat_id= message.from_user.id, text='Напоминание успешно удалено', reply_markup=keyboard)
        connection.close()
        inlkb = inline_keyboard_for_delete('delete')
        #Изменение текста в сообщении
        await bot.edit_message_text(chat_id=call.from_user.id,message_id=call.message.message_id, text='Напоминание успешно удалено.')
        #Изменение клавиатуры. Id пользователя, Id сообщения, новая форма
        await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=inlkb)
    elif call.data.split('_')[1] == 'editDescription':
        keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton('🔙Отмена'))
        await bot.send_message(call.from_user.id, '📃Введите новое описание.', reply_markup=keyboard)
        await FSMEditReminder.description.set()
    elif call.data.split('_')[1] == 'editDate':
        keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton('🔙Отмена'))
        await bot.send_message(call.from_user.id, '📅Введите новую дату.\nФормат написания даты (дд.мм.гггг).', reply_markup=keyboard)
        await FSMEditReminder.date.set()
    elif call.data.split('_')[1] == 'editTime':
        keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton('🔙Отмена'))
        await bot.send_message(call.from_user.id, '⏱Введите новое время.\nФормат написания времени (чч:мм).', reply_markup=keyboard)
        await FSMEditReminder.time.set()
    #Кнопка возврата к списку напоминаний
    elif call.data.split('_')[1] == 'back':
            #Подключение базы данных
            connection = pymysql.connect(
                host='localhost',
                port=3306,
                user='root',
                password='qwert123',
                database='reminder_bot',
                cursorclass=pymysql.cursors.DictCursor
            )    
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM reminder_bot.info_table WHERE `user_id` = '{call.from_user.id}' ORDER BY `date` ASC, `time` ASC")
                bd = cursor.fetchall()
                if not bd: #bd is None
                    await bot.edit_message_text(chat_id=call.from_user.id,message_id=call.message.message_id, text='😐У вас нет напоминаний.')
                else:
                    ansMsg = '📄Список напоминаний:\n\n'
                    id_reminder=[]
                    for i in range(len(bd)):
                        id_reminder.append(bd[i]['id_reminder'])
                        ansMsg += str(i+1) + '. ' + bd[i]['description'] + ' (' + str(bd[i]['date']) + ' ' +  ' в ' + bd[i]['time'] + ')' + '\n'
                    ansMsg += '\n'
                    ansMsg += 'Выберите номер для редактирования:👇'
                    #Вызов формы для редактирования
                    inlkb = inline_keyboard_for_delete('start', len(bd), ' ', id_reminder)
                    #Изменение текста в сообщении
                    await bot.edit_message_text(chat_id=call.from_user.id,message_id=call.message.message_id, text=ansMsg)
                    #Изменение клавиатуры. Id пользователя, Id сообщения, новая форма
                    await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=inlkb)    
            connection.close()



#Изменение описания
@dp.message_handler(state=FSMEditReminder.description)
async def load_description(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if len(message.text) <= 100 and (data['oldDescription'] != message.text):
            data['newDescription'] = message.text
            connection = pymysql.connect(
                host='localhost',
                port=3306,
                user='root',
                password='qwert123',
                database='reminder_bot',
                cursorclass=pymysql.cursors.DictCursor
            )
            #Запись в БД
            with connection.cursor() as cursor:
                cursor.execute(f"UPDATE reminder_bot.info_table SET `description` = '{data['newDescription']}' WHERE `id_reminder` = {data['id_reminder']}")
                connection.commit()
                inlkb = inline_keyboard_for_delete('editDescription')

                cursor.execute(f"SELECT * FROM reminder_bot.info_table WHERE `user_id` = '{message.from_user.id}' ORDER BY `date` ASC, `time` ASC")
                bd = cursor.fetchall()
                if not bd: #bd is None
                    await bot.edit_message_text(chat_id=message.from_user.id,message_id=message.message_id, text='😐У вас нет напоминаний.')
                else:
                    ansMsg = '📄Список напоминаний:\n\n'
                    id_reminder=[]
                    for i in range(len(bd)):
                        id_reminder.append(bd[i]['id_reminder'])
                        ansMsg += str(i+1) + '. ' + bd[i]['description'] + ' (' + str(bd[i]['date']) + ' ' +  ' в ' + bd[i]['time'] + ')' + '\n'
                    ansMsg += '\n'
                    ansMsg += 'Выберите номер для редактирования:👇'
                    #Вызов формы для редактирования
                    inlkb = inline_keyboard_for_delete('start', len(bd), ' ', id_reminder)
                    #Изменение текста в сообщении
                    await bot.edit_message_text(chat_id=message.from_user.id,message_id=data['message_id'], text=ansMsg)
                    #Изменение клавиатуры. Id пользователя, Id сообщения, новая форма
                    await bot.edit_message_reply_markup(message.from_user.id, data['message_id'], reply_markup=inlkb)
                await state.finish()
            connection.close()
            keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton('Создать напоминание')).add(KeyboardButton('Мои напоминания'))
            await bot.send_message(chat_id= message.from_user.id, text='Описание успешно изменено.', reply_markup=keyboard)
        else:
            await bot.send_message(chat_id= message.from_user.id, text='😐Размер сообщения не может превышать более 100 символов.\nТак же написанное вами новое описание не должно совпадать со старым.❗\nПопробуйте еще раз')
    


#Изменение даты
@dp.message_handler(state=FSMEditReminder.date)
async def buttons(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if len(message.text) == 10 and (data['oldDate'] != message.text):
                correctDate = False
                try:
                    y = int(message.text.split('.')[2])
                    m = int(message.text.split('.')[1])
                    d = int(message.text.split('.')[0])
                    correct_date = f'{y}-{m}-{d}'
                    date(y, m, d)
                    nowDate = datetime.now()
                    
                    if (y == nowDate.year and m == nowDate.month and d >= nowDate.day) or (y > nowDate.year) or  (y == nowDate.year and m > nowDate.month):
                        correctDate = True
                    else:
                        correctDate = False
                except:
                    correctDate = False
                if correctDate:
                    data['newDate'] = correct_date
                    connection = pymysql.connect(
                        host='localhost',
                        port=3306,
                        user='root',
                        password='qwert123',
                        database='reminder_bot',
                        cursorclass=pymysql.cursors.DictCursor
                    )
                    #Запись в БД
                    with connection.cursor() as cursor:
                        cursor.execute(f"UPDATE reminder_bot.info_table SET `date` = '{data['newDate']}' WHERE `id_reminder` = {data['id_reminder']}")
                        connection.commit()
                        inlkb = inline_keyboard_for_delete('editDate', ' ', data['id_reminder'])
                        cursor.execute(f"SELECT * FROM reminder_bot.info_table WHERE `user_id` = '{message.from_user.id}' ORDER BY `date` ASC, `time` ASC")
                        bd = cursor.fetchall()
                        if not bd: #bd is None
                            await bot.edit_message_text(chat_id=message.from_user.id,message_id=message.message_id, text='😐У вас нет напоминаний.')
                        else:
                            ansMsg = '📄Список напоминаний:\n\n'
                            id_reminder=[]
                            for i in range(len(bd)):
                                id_reminder.append(bd[i]['id_reminder'])
                                ansMsg += str(i+1) + '. ' + bd[i]['description'] + ' (' + str(bd[i]['date']) + ' ' +  ' в ' + bd[i]['time'] + ')' + '\n'
                            ansMsg += '\n'
                            ansMsg += 'Выберите номер для редактирования:👇'
                            #Вызов формы для редактирования
                            inlkb = inline_keyboard_for_delete('start', len(bd), ' ', id_reminder)
                    connection.close()
                    #Изменение текста в сообщении
                    await bot.edit_message_text(chat_id=message.from_user.id,message_id=data['message_id'], text=ansMsg)
                    #Изменение клавиатуры. Id пользователя, Id сообщения, новая форма
                    await bot.edit_message_reply_markup(message.from_user.id, data['message_id'], reply_markup=inlkb)
                    await state.finish()
                    keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton('Создать напоминание')).add(KeyboardButton('Мои напоминания'))
                    await bot.send_message(chat_id= message.from_user.id, text='Дата успешно изменена.', reply_markup=keyboard)
                else:
                    await bot.send_message(chat_id= message.from_user.id, text='😐Вы ввели неправильную дату. \nПопробуйте еще раз. Дата должна быть в будущем времени. \nФормат написания даты (дд.мм.гггг).Так же написанное вами новая дата не должна совпадать со старой.❗')
        else:
            await bot.send_message(chat_id= message.from_user.id, text='😐Размер сообщения должен быть 10 символов.\nФормат написания даты (дд.мм.гггг).\nПопробуйте еще раз.\nТак же написанное вами новая дата не должна совпадать со старой.❗')



#Изменение времени
@dp.message_handler(state=FSMEditReminder.time)
async def buttons(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if len(message.text) == 5 and (data['oldTime'] != message.text):
                try:
                    hour = message.text.split(':')[0]
                    min = message.text.split(':')[1]
                    y = int(data['date'].split('.')[2])
                    m = int(data['date'].split('.')[1])
                    d = int(data['date'].split('.')[0])
                    nowDate = datetime.now()
                    data['newTime'] = message.text
                    if int(hour) <= 23 and int(min) <= 59:
                        if nowDate.year == y and nowDate.month == m and nowDate.day == d:    
                            if nowDate.hour < int(hour) or (nowDate.hour == int(hour) and nowDate.minute < int(min)):
                                connection = pymysql.connect(
                                    host='localhost',
                                    port=3306,
                                    user='root',
                                    password='qwert123',
                                    database='reminder_bot',
                                    cursorclass=pymysql.cursors.DictCursor
                                )
                                #Запись в БД
                                with connection.cursor() as cursor:
                                    cursor.execute(f"UPDATE reminder_bot.info_table SET `time` = '{data['newTime']}' WHERE `id_reminder` = {data['id_reminder']}")
                                    connection.commit()
                                    inlkb = inline_keyboard_for_delete('editTime', ' ', data['id_reminder'])
                                    cursor.execute(f"SELECT * FROM reminder_bot.info_table WHERE `user_id` = '{message.from_user.id}' ORDER BY `date` ASC, `time` ASC")
                                    bd = cursor.fetchall()
                                    if not bd: #bd is None
                                        await bot.edit_message_text(chat_id=message.from_user.id,message_id=message.message_id, text='😐У вас нет напоминаний.')
                                    else:
                                        ansMsg = '📄Список напоминаний:\n\n'
                                        id_reminder=[]
                                        for i in range(len(bd)):
                                            id_reminder.append(bd[i]['id_reminder'])
                                            ansMsg += str(i+1) + '. ' + bd[i]['description'] + ' (' + str(bd[i]['date']) + ' ' +  ' в ' + bd[i]['time'] + ')' + '\n'
                                        ansMsg += '\n'
                                        ansMsg += 'Выберите номер для редактирования:👇'
                                        #Вызов формы для редактирования
                                        inlkb = inline_keyboard_for_delete('start', len(bd), ' ', id_reminder)
                                connection.close()
                                #Изменение текста в сообщении
                                await bot.edit_message_text(chat_id=message.from_user.id,message_id=data['message_id'], text=ansMsg)
                                #Изменение клавиатуры. Id пользователя, Id сообщения, новая форма
                                await bot.edit_message_reply_markup(message.from_user.id, data['message_id'], reply_markup=inlkb)
                                #Закрыть состояние
                                await state.finish()
                            else:
                                await bot.send_message(chat_id= message.from_user.id, text='😐Вы ввели неправильное время. \nПопробуйте еще раз. Время должно быть в будущем. \nФормат написания времени (чч:мм)')
                        else:
                            connection = pymysql.connect(
                                host='localhost',
                                port=3306,
                                user='root',
                                password='qwert123',
                                database='reminder_bot',
                                cursorclass=pymysql.cursors.DictCursor
                            )
                            #Запись в БД
                            with connection.cursor() as cursor:
                                cursor.execute(f"UPDATE reminder_bot.info_table SET `time` = '{data['newTime']}' WHERE `id_reminder` = {data['id_reminder']}")
                                connection.commit()
                                inlkb = inline_keyboard_for_delete('editTime', ' ', data['id_reminder'])
                                cursor.execute(f"SELECT * FROM reminder_bot.info_table WHERE `user_id` = '{message.from_user.id}' ORDER BY `date` ASC, `time` ASC")
                                bd = cursor.fetchall()
                                if not bd: #bd is None
                                    await bot.edit_message_text(chat_id=message.from_user.id,message_id=message.message_id, text='😐У вас нет напоминаний.')
                                else:
                                    ansMsg = '📄Список напоминаний:\n\n'
                                    id_reminder=[]
                                    for i in range(len(bd)):
                                        id_reminder.append(bd[i]['id_reminder'])
                                        ansMsg += str(i+1) + '. ' + bd[i]['description'] + ' (' + str(bd[i]['date']) + ' ' +  ' в ' + bd[i]['time'] + ')' + '\n'
                                    ansMsg += '\n'
                                    ansMsg += 'Выберите номер для редактирования:👇'
                                    #Вызов формы для редактирования
                                    inlkb = inline_keyboard_for_delete('start', len(bd), ' ', id_reminder)
                            connection.close()
                            #Изменение текста в сообщении
                            await bot.edit_message_text(chat_id=message.from_user.id,message_id=data['message_id'], text=ansMsg)
                            #Изменение клавиатуры. Id пользователя, Id сообщения, новая форма
                            await bot.edit_message_reply_markup(message.from_user.id, data['message_id'], reply_markup=inlkb)
                            #Закрыть состояние
                            await state.finish()
                        keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton('Создать напоминание')).add(KeyboardButton('Мои напоминания'))
                        await bot.send_message(chat_id= message.from_user.id, text='Время успешно изменено.', reply_markup=keyboard)
                    else:
                        await bot.send_message(chat_id= message.from_user.id, text='😐Вы ввели неправильное время. \nПопробуйте еще раз. Время должно быть в будущем. \nФормат написания времени (чч:мм)\nТак же написанное вами новое время не должно совпадать со старым.❗')
                except:
                    await bot.send_message(chat_id= message.from_user.id, text='😐Вы ввели неправильное время. \nПопробуйте еще раз. Время должно быть в будущем. \nФормат написания времени (чч:мм)\nТак же написанное вами новое время не должно совпадать со старым.❗')
        else:
            await bot.send_message(chat_id= message.from_user.id, text='😐Размер сообщения должен быть 5 символов.\nФормат написания времени (чч:мм).\nПопробуйте еще раз.\nТак же написанное вами новое время не должно совпадать со старым.❗')



#Вывод несуществующих команд
@dp.message_handler()
async def cancel_handler(message: types.Message, state):
    await message.answer('🥱Возможно вы ввели неправильную команду.')



async def checker_reminer():
    while True:
        #Подключение базы данных
        connection = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='qwert123',
            database='reminder_bot',
            cursorclass=pymysql.cursors.DictCursor
        )    
        with connection.cursor() as cursor:
            #Дата
            date_today = str(datetime.now().date()).split('-')[-1] + '.' + str(datetime.now().date()).split('-')[1] + '.' + str(datetime.now().date()).split('-')[0]
            dateToday = f'{date_today.split(".")[2]}-{date_today.split(".")[1]}-{date_today.split(".")[0]}'
            #Время
            hour = str(datetime.now().hour)
            if len(hour) == 1:
                hour = '0' + hour
            minute = str(datetime.now().minute)
            if len(minute) == 1:
                minute = '0' + minute
            time_now = hour + ':' + minute

            cursor.execute(f"SELECT * FROM reminder_bot.info_table WHERE `date` <= '{dateToday}' AND `time` <= '{time_now}'") 
            bd = cursor.fetchall()
            if len(bd):
                for i in range(len(bd)):
                    await bot.send_message(bd[i]['user_id'], f"📣Напоминание\n\n{bd[i]['description']}")
                    cursor.execute(f"DELETE FROM reminder_bot.info_table WHERE  `id_reminder` = {bd[i]['id_reminder']}")
                    connection.commit() 
            
        connection.close()
        #Таймер 
        await asyncio.sleep(20)

 
if __name__ == '__main__':

    #Запуск асинх. функции для оповещения пользователей
    asyncio.get_event_loop().create_task(checker_reminer())
    
    #Запуск бота
    executor.start_polling(dp, skip_updates = True)