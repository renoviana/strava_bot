from datetime import datetime
import mongoengine
import telebot
from telebot.util import quick_markup

from application.commands.streak import handle_streak_command
from application.commands.frequency import (
  handle_month_frequency_command,
  handle_year_frequency_command
)
from application.commands.rank import (
  handle_rank_month_command,
  handle_rank_year_command,
  handle_rank_menu
)
from application.commands.medal import handle_medal_command
from application.commands.admin import (
  handle_admin_callback,
  handle_admin_command,
  handle_reset_command
)
from config import MONGO_URI, REDIRECT_URI, STRAVA_CLIENT_ID, TELEGRAM_TOKEN

mongoengine.connect(host=MONGO_URI)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def rank_command_menu(group_id :int, command :str, start :datetime, end :datetime):
    sport_type_list = handle_rank_menu(group_id, start, end)
    markup_dict = {x:{'callback_data': f'{command}_{x}'} for x in sport_type_list}
    markup = quick_markup(markup_dict, row_width=1)
    bot.send_message(group_id, "Selecione o tipo de esporte:", reply_markup=markup)

@bot.message_handler(commands=['admin'])
def admin_command_handler(message):
    group_id = message.chat.id
    member_list = handle_admin_command(group_id)
    markup_dict = {}
    for member in member_list:
        member_name, member_id = member
        markup_dict[member_name] = {
            'callback_data': f'admin_{member_id}'
        }
    markup = quick_markup(markup_dict, row_width=2)
    bot.send_message(group_id, "Selecione um membro pra remover:", reply_markup=markup)

@bot.message_handler(commands=['frequency'])
def frequency_command_handler(message):
    group_id = message.chat.id
    bot.send_message(group_id, handle_month_frequency_command(group_id), parse_mode='HTML', disable_web_page_preview=True)


@bot.message_handler(commands=['yfrequency'])
def year_frequency_command_handler(message):
    group_id = message.chat.id
    bot.send_message(group_id, handle_year_frequency_command(group_id), parse_mode='HTML', disable_web_page_preview=True)

@bot.message_handler(commands=['medalhas'])
def medal_command_handler(message):
    group_id = message.chat.id
    bot.send_message(group_id, handle_medal_command(group_id), parse_mode='HTML', disable_web_page_preview=True)

@bot.message_handler(commands=['rank', 'yrank'])
def rank_command_handler(message):
    group_id = message.chat.id
    command = message.text.strip().lower().split('/')[-1]
    if command.startswith('rank'):
        start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start.month != 12:
            end = start.replace(month=start.month % 12 + 1)
        else:
            end = start.replace(year=start.year + 1, month=1)
        return rank_command_menu(group_id, command, start, end)
    
    start = datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    end = start.replace(year=start.year + 1)
    rank_command_menu(group_id, command, start, end)

@bot.message_handler(commands=['streak'])
def streak_command_handler(message):
    group_id = message.chat.id
    bot.send_message(group_id, handle_streak_command(group_id), parse_mode='HTML', disable_web_page_preview=True)

@bot.message_handler(commands=['link'])
def link_command_handler(message):
    group_id = message.chat.id
    strava_client_id = STRAVA_CLIENT_ID
    redirect_uri = REDIRECT_URI.format(group_id)
    bot.send_message(group_id,
        f"https://www.strava.com/oauth/authorize?client_id={strava_client_id}&redirect_uri={redirect_uri}&response_type=code&scope=activity:read"
    )

@bot.message_handler(commands=['reset'])
def reset_command_handler(message):
    group_id = message.chat.id
    bot.send_message(group_id, handle_reset_command(group_id), parse_mode='HTML', disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('rank_'))
def rank_month_callback_handler(call):
    group_id = call.message.chat.id
    sport_type = call.data.split('_')[1]
    bot.send_message(group_id, handle_rank_month_command(group_id, sport_type), parse_mode='HTML', disable_web_page_preview=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith('yrank_'))
def rank_year_callback_handler(call):
    group_id = call.message.chat.id
    sport_type = call.data.split('_')[1]
    bot.send_message(group_id, handle_rank_year_command(group_id, sport_type), parse_mode='HTML', disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def admin_callback_handler(call):
    group_id = call.message.chat.id
    member_id = int(call.data.split('_')[1])
    user_name_admin = call.from_user.first_name or call.from_user.username
    bot.send_message(group_id, handle_admin_callback(group_id, member_id, user_name_admin), parse_mode='HTML', disable_web_page_preview=True)

def start_bot():
    bot.polling()
