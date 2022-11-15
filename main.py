import telebot
from telebot import types
import time

token = '5617522808:AAEVpKPx6fJqwoZDjmvuyhUBSQe41TA-lMs'
bot = telebot.TeleBot(token)
@bot.message_handler(commands=['start'])
def start(message):
    mess = f'<b>Привет</b>, {message.from_user.first_name}'
    mess1 = f'описание бота'
    bot.send_message(message.chat.id, mess, parse_mode='html')
    bot.send_message(message.chat.id, mess1, parse_mode='html')

@bot.message_handler(commands=['help'])
def website(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    website = types.KeyboardButton('Сайт универа')
    markup.add(website)
    bot.send_message(message.chat.id, 'Посетить веб сайт?', reply_markup=markup)

@bot.message_handler()
def get_user_text(message):
    if message.text == 'Бот напомни':
        bot.send_message(message.chat.id, 'О чем вам напомнить?', parse_mode='html')
        text = str(input(message.id))
        bot.send_message(message.chat.id, 'Через сколько минут вам напомнить?', parse_mode='html')
        local_time = input(type(int(message.id)))
        local_time = local_time * 60
        time.sleep(local_time)
        bot.send_message(message.chat.id, f'+text', parse_mode='html')
print('sos')

bot.polling(none_stop=True, interval=0)
