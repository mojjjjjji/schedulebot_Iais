from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime


def inline_keyboard_for_delete(name_form=None, counts=None, number=None, id_reminder=None):
    if name_form == 'start':
        key_num = ()
        form = InlineKeyboardMarkup()
        for count in range(counts):
                key_num += (InlineKeyboardButton(count+1, callback_data=str(id_reminder[count]) +'_number'),)
        form.row(*key_num)
        return form
    elif name_form == 'number':
        form = InlineKeyboardMarkup()
        form.row(InlineKeyboardButton('🔧Редактировать', callback_data=str(number) +'_edit'),InlineKeyboardButton('🚫Удалить', callback_data=str(number) +'_delete'))
        form.add(InlineKeyboardButton('🔙Вернуться к списку', callback_data='key_back'))
        return form
    #Редактирование
    elif name_form == 'edit':
        form = InlineKeyboardMarkup()
        form.row(InlineKeyboardButton('📃Описание', callback_data=str(number) +'_editDescription'),InlineKeyboardButton('📅Дату', callback_data=str(number) +'_editDate'),InlineKeyboardButton('⏱Время', callback_data=str(number) +'_editTime'))
        #form.add(InlineKeyboardButton('Сразу все', callback_data='editAll'))
        form.add(InlineKeyboardButton('🔙Вернуться к списку', callback_data='key_back'))
        return form
    #Удаление
    elif name_form == 'delete':
        form = InlineKeyboardMarkup()
        form.add(InlineKeyboardButton('🔙Вернуться к списку', callback_data='key_back'))
        return form
    elif name_form == 'editDescription':
        form = InlineKeyboardMarkup()
        form.add(InlineKeyboardButton('🔙Вернуться к списку', callback_data='key_back'))
        return form
    elif name_form == 'editDate':
        form = InlineKeyboardMarkup()
        form.add(InlineKeyboardButton('🔙Вернуться к списку', callback_data='key_back'))
        return form
    elif name_form == 'editTime':
        form = InlineKeyboardMarkup()
        form.add(InlineKeyboardButton('🔙Вернуться к списку', callback_data='key_back'))
        return form