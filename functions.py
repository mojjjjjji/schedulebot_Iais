from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
#Создание формы для заполнения даты и времени
def mode_inline_keyboard(text=None, call_data=None, row=None, current_form=None):
    if text == None and call_data == None and row == None and current_form == None:
        months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
        touple_mon = ()
        form = InlineKeyboardMarkup()
        form.add(InlineKeyboardButton('Год:', callback_data='year_text'))
        form.row(InlineKeyboardButton(str(datetime.today().year), callback_data='save_yearResult'), InlineKeyboardButton('➕', callback_data='plus_year'), InlineKeyboardButton('➖', callback_data='minus_year'))
        
        form.add(InlineKeyboardButton('Месяц:', callback_data='month_text'))
        form.add(InlineKeyboardButton('Выберите месяц 👇', callback_data='save_monthResult'))

        for mon in months[:4]:
            touple_mon += (InlineKeyboardButton(mon, callback_data=str(months.index(mon))+'_month'),)
        
        form.row(*touple_mon)
        touple_mon = ()

        for mon in months[4:8]:
            touple_mon += (InlineKeyboardButton(mon, callback_data=str(months.index(mon))+'_month'),)

        form.row(*touple_mon)
        touple_mon = ()

        for mon in months[8:]:
            touple_mon += (InlineKeyboardButton(mon, callback_data=str(months.index(mon))+'_month'),)
        
        form.row(*touple_mon)

        form.add(InlineKeyboardButton('День:', callback_data='day_text'))
        form.row(InlineKeyboardButton(str(datetime.today().day), callback_data='save_dayResult'), InlineKeyboardButton('➕', callback_data='plus_day'), InlineKeyboardButton('➖', callback_data='minus_day'))
        
        hour = str(datetime.now().hour)
        if len(hour) == 1:
            hour = '0' + hour
        minute = str(datetime.now().minute)
        if len(minute) == 1:
            minute = '0' + minute

        form.add(InlineKeyboardButton('Время:', callback_data='time_text'))
        form.row(InlineKeyboardButton(hour, callback_data='save_hourResult'), InlineKeyboardButton('➕', callback_data='plus_hour'), InlineKeyboardButton('➖', callback_data='minus_hour'))
        form.row(InlineKeyboardButton(minute, callback_data='save_minuteResult'), InlineKeyboardButton('➕', callback_data='plus_minute'), InlineKeyboardButton('➖', callback_data='minus_minute'))

        form.add(InlineKeyboardButton('✅ Сохранить', callback_data='save_but'))

        return form

    else:
        #Изменение кнопки
        current_form['inline_keyboard'][row][0] = InlineKeyboardButton(text, callback_data=call_data)
        return current_form
