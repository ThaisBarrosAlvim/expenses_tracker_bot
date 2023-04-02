import calendar
import json
import os

import telebot
import datetime
from math import ceil

from decouple import config
from telebot import types

bot = telebot.TeleBot(config('BOT_TOKEN'))

# Variables to store the current expense and the budged expense
current_expense = 0
monthly_budged = 600
daily_expense = {}


# Change the file name based on the user
def get_file_name(user_id):
    return os.path.join('data', str(user_id) + '_json_data.json')


def load_data(user_id):
    global daily_expense
    if daily_expense == {}:
        filename = get_file_name(user_id)
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as json_file:
                    daily_expense = json.load(json_file, object_hook=jsonk2int)  # convert the keys/values to int
            except json.decoder.JSONDecodeError:
                print('Error loading the daily_expense data.')
                os.remove(filename)
            print('daily_expense, loaded: ', daily_expense)
        else:
            print('daily_expense, not loaded')


# Change the file name based on the user
def save_data(user_id):
    filename = get_file_name(user_id)
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    with open(filename, 'w') as json_file:
        json.dump(daily_expense, json_file)


# Returns the week of the month for the specified date.
def week_of_month(dt):
    first_day = dt.replace(day=1)

    dom = dt.day
    adjusted_dom = dom + first_day.weekday()

    return int(ceil(adjusted_dom / 7.0))


# used to convert the keys of the json file to int
def jsonk2int(x):
    if isinstance(x, dict):
        return {int(k): v for k, v in x.items()}
    return x


# Function to recalculate the monthly maximum expense
def recalculate_monthly_budged(message):
    global monthly_budged
    try:
        monthly_budged = float(message.text.replace(',', '.'))
        bot.send_message(chat_id=message.chat.id, text=f'The monthly budged has been updated to '
                                                       f'R${monthly_budged:.2f}.')
    except ValueError:
        bot.reply_to(message, 'The value entered is not a number.')


# Function to handle the command /recalculate_monthly_budged
@bot.message_handler(commands=['recalculate_monthly_budged'])
def handle_recalculate_monthly_budged(message):
    resp = bot.send_message(message.chat.id, 'Please, send the new value for the monthly budged:',
                            reply_markup=telebot.types.ForceReply(selective=False))

    bot.register_next_step_handler(resp, recalculate_monthly_budged)


# { 2023: { 1: { 1: [1, 2, 3], 2: [1, 2, 3] } } }
def update_day_expense(dt, value=None, save=False, user_id=None):
    year = dt.year
    month = dt.month
    day = dt.day

    if year not in daily_expense:
        daily_expense[year] = {}
    if month not in daily_expense[year]:
        daily_expense[year][month] = {}
    if day not in daily_expense[year][month]:
        daily_expense[year][month][day] = []

    if value != 0:
        if value is not None:
            daily_expense[year][month][day].append(value)
        if save:
            save_data(user_id)


def handle_set_day_expense_step3(message, dt: datetime.datetime):
    try:
        value = float(message.text.replace(',', '.'))
    except ValueError:
        bot.send_message(chat_id=message.chat.id,
                         text='Please, send a valid number:',
                         reply_markup=telebot.types.ForceReply(selective=False))
        bot.register_next_step_handler(message, handle_set_day_expense_step3, dt)
    else:
        update_day_expense(dt, value, save=True, user_id=message.chat.id)
        bot.send_message(chat_id=message.chat.id,
                         text='The expense has been set.')


def handle_set_day_expense_step2(message, markup):
    try:
        dt = datetime.datetime.strptime(message.text, '%d/%m/%y')
    except ValueError:
        bot.send_message(chat_id=message.chat.id,
                         text='Please, send a valid date in format: dd/mm/yy (ex: "02/07/23"):',
                         reply_markup=markup)
        bot.register_next_step_handler(message, handle_set_day_expense_step2)
    else:
        bot.send_message(chat_id=message.chat.id, text='Please, send the value:',
                         reply_markup=telebot.types.ForceReply(selective=False))
        bot.register_next_step_handler(message, handle_set_day_expense_step3, dt=dt)


@bot.message_handler(commands=['get_report'])
def get_report(message):
    filename = get_file_name(message.chat.id)
    if os.path.exists(filename):
        bot.send_document(chat_id=message.chat.id, document=open(filename, 'rb'))
    else:
        bot.send_message(chat_id=message.chat.id, text='There is no data to send.')


@bot.message_handler(commands=['reset_all'])
def reset_all(message):
    global daily_expense
    daily_expense = {}
    save_data(message.chat.id)
    bot.send_message(chat_id=message.chat.id, text='All data has been reset.')


@bot.message_handler(commands=['set_day_expense'])
def handle_set_day_expense_step1(message):
    markup = types.ReplyKeyboardMarkup()
    current_day = datetime.datetime.now()
    item2dayback = types.KeyboardButton((current_day - datetime.timedelta(days=2)).strftime('%d/%m/%y'))
    item1dayback = types.KeyboardButton((current_day - datetime.timedelta(days=1)).strftime('%d/%m/%y'))
    item1daynext = types.KeyboardButton((current_day + datetime.timedelta(days=1)).strftime('%d/%m/%y'))
    item2daynext = types.KeyboardButton((current_day + datetime.timedelta(days=2)).strftime('%d/%m/%y'))
    markup.row(item2dayback, item1dayback)
    markup.row(item1daynext, item2daynext)
    resp = bot.send_message(message.chat.id,
                            'Please, send the date (format: dd/mm/yy) that you want to set the expense:',
                            reply_markup=markup)

    bot.register_next_step_handler(resp, handle_set_day_expense_step2, markup=markup)


# Function to handle the received message
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    load_data(message.chat.id)
    global current_expense, daily_expense
    try:
        if message.text in ['/reprint', '/start']:
            value = 0
        else:
            value = float(message.text.replace(',', '.'))
    except ValueError:
        bot.send_message(chat_id=message.chat.id,
                         text='Please, send a valid number or the \'start_month\' command to reset the count.')
    else:
        current_expense += value
        current_date = datetime.datetime.now()

        # Create date if don't exist
        update_day_expense(current_date, value, save=True, user_id=message.chat.id)
        daily_expense_value = sum(daily_expense[current_date.year][current_date.month][current_date.day])
        monthly_expense_value = sum(sum(d) for d in daily_expense[current_date.year][current_date.month].values())

        value_left = monthly_budged - current_expense
        value_left_today = (monthly_budged / calendar.monthrange(current_date.year, current_date.month)[1]) \
                           - daily_expense_value
        value_left_week = (monthly_budged / 4) - value
        weekly_expense_value = sum(sum(ld) for d, ld in daily_expense[current_date.year][current_date.month].items() if
                                   week_of_month(datetime.datetime(current_date.year, current_date.month, d)) ==
                                   week_of_month(current_date))
        current_week = week_of_month(current_date)

        # send the message printing the output
        text = (
            # Day
                f'Sum of {current_date.strftime("%A %d %B")}: R${daily_expense_value:.2f} '
                + (
                    f'(R$ {value_left_today:.2f} remaning)' if value_left_today >= 0
                    else f'<ins>(over R${-1 * value_left_today:.2f})</ins>')
                # Week
                + f'\nSum of this week ({current_week}th week): R${weekly_expense_value:.2f} '
                + (
                    f'(R$ {value_left_week:.2f} remaning)' if value_left_week >= 0
                    else f'<ins>(over R${-1 * value_left_week:.2f})</ins>')
                # Month
                + f'\nSum of {current_date.strftime("%B")} ({current_date.strftime("%m/%y")}): R$ {monthly_expense_value:.2f}'
                + (
                    f' (R$ {value_left:.2f} remaning)' if value_left >= 0 else f' <ins>({-1 * value_left:.2f} over)</ins>'))
        bot.send_message(chat_id=message.chat.id, text=text, parse_mode="HTML")


bot.polling()
