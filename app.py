API_KEY = "5694590247:AAEDwug01HoBKJOrkFrXfi1_Klo7DAXeNPs"


#import libraries
from skimage.io import imread
import telebot
from telebot import types
import pickle
import string
import numpy as np
import sqlite3

from util import JSONParser
from util import process_image

#global variable
user_data = {}

# database connect
conn = sqlite3.connect('./data/data_sepatu.db', check_same_thread=False)
conn.row_factory = lambda cursor, row: row[0]
cur = conn.cursor()

#load model
with open('model/model_chatbot.pkl', 'rb') as handle:
    model = pickle.load(handle)

#API Telegram Bot
bot = telebot.TeleBot(API_KEY)

# load data
path = "data/intents.json"
jp = JSONParser()
jp.parse(path)
df = jp.get_dataframe()


def preprocess(chat):
    # lowercase transform
    chat = chat.lower()
    tandabaca = tuple(string.punctuation)
    chat = "".join(ch for ch in chat if ch not in tandabaca)
    return chat


"""
generate button with items from the database
"""


def makeButtons(user):

    markup = types.InlineKeyboardMarkup()
    if (user.get('buy_state') == 'gender'):
        selected = cur.execute("SELECT DISTINCT gender FROM shoes").fetchall()
        for button in selected:
            btt = types.InlineKeyboardButton(text=button, callback_data=button)
            markup.row(btt)

    if (user.get('buy_state') == 'brand'):
        selected = cur.execute(
            f"SELECT DISTINCT brand FROM shoes WHERE gender ='{user.get('gender')}'"
        ).fetchall()
        for button in selected:
            btt = types.InlineKeyboardButton(text=button, callback_data=button)
            markup.row(btt)

    if (user.get('buy_state') == 'shoe_name'):
        selected = cur.execute(
            f"SELECT name FROM shoes WHERE gender = '{user.get('gender')}' and brand = '{user.get('brand')}'"
        ).fetchall()

        for button in selected:
            btt = types.InlineKeyboardButton(text=button, callback_data=button)
            markup.row(btt)

    if (user.get('buy_state') == 'color'):
        selected = cur.execute(
            f"SELECT DISTINCT color FROM shoes WHERE gender = '{user.get('gender')}' and brand = '{user.get('brand')}'and name = '{user.get('name')}'"
        ).fetchall()

        for button in selected:
            btt = types.InlineKeyboardButton(text=button, callback_data=button)
            markup.row(btt)

    return markup


# function for updating
def update_user(user, key, value):
    print(user)
    user[key] = value


def resetUser(user):
    user = {}


# function to update bot state
def update_state(chat, pipe, user):
    global bot_state
    chat = preprocess(chat)
    res = pipe.predict_proba([chat])
    max_prob = max(res[0])
    if max_prob < .2:
        user['bot_state'] = 'error'
        bot_state = 'error'
    else:
        max_id = np.argmax(res[0])
        pred_tag = pipe.classes_[max_id]
        user['bot_state'] = pred_tag
        bot_state = pred_tag


def bot_response(jp):
    global bot_state
    if bot_state == "error":
        return "Maaf kak bisa Diperjelas lagi ngga kak masalahnya ? \n\
        saya kurang paham :(", None
    else:
        return jp.get_response(bot_state), bot_state


"""
Handling all message that send to machine
and handle the input process and become the response of the bot
"""


@bot.message_handler(regexp='[a-z]+')
def greet(message):
    global user_data

    #set state user
    user_data[str(message.from_user.id)] = user_data.get(
        str(message.from_user.id), {})
    user = user_data[str(
        message.from_user.id)]  #get unique user id and its data

    if (user.get('bot_state') is None and message.text == '/start'):
        update_user(user, 'bot_state', 'start')
        bot.reply_to(
            message,
            "selamat datang di pelayanan pembelian Get Shoe, ada yang bisa dibantu ?"
        )
    else:
        update_state(message.text, model, user)
        print(message.text)
        bot.reply_to(message, bot_response(jp))
        
        if (user.get("bot_state") == 'cancel'):
            resetUser(message.from_user.id)

        if (user.get('bot_state') == 'beli' and user.get('buy_state') is None):
            update_user(user, 'buy_state', 'gender')
            bot.send_message(message.chat.id,
                             "Pilih Gender",
                             reply_markup=makeButtons(user))


# proses beli
"""
Handling shoping session
1. choose gender
2. Choose brand
3. choose shoe name
4. choose color
5. size
"""


@bot.callback_query_handler(func=lambda call: True)
def callback_brand(call):
    global user_data
    user = user_data[str(call.from_user.id)]  #get unique user id and its data

    if (user.get('bot_state') == 'beli'):
        if (user.get('buy_state') == "gender"):
            update_user(user, 'gender', call.data)
            update_user(user, 'buy_state', 'brand')
            bot.send_message(call.message.chat.id,
                             "Pilih Merek Sepatu",
                             reply_markup=makeButtons(user))

        if (user.get('buy_state') == "brand"
                and user.get('gender') is not call.data):
            update_user(user, 'brand', call.data)
            update_user(user, 'buy_state', 'shoe_name')
            bot.send_message(call.message.chat.id,
                             "Pilih Nama Sepatu",
                             reply_markup=makeButtons(user))

        if (user.get('buy_state') == "shoe_name"
                and user.get('brand') is not call.data):
            update_user(user, 'name', call.data)
            update_user(user, 'buy_state', 'color')
            bot.send_message(call.message.chat.id,
                             "Pilih Warna Sepatu",
                             reply_markup=makeButtons(user))

        if (user.get('buy_state') == "color"
                and user.get('name') is not call.data):
            update_user(user, 'color', call.data)
            update_user(user, 'buy_state', 'size')
            print(str(user))
            bot.send_message(
                call.message.chat.id,
                "Kita Bantu Pilih ukuran Sepatunya ya kak ?\n coba kakak kirimin foto kaki kakak diatas kertas HVS A4, seperti contoh berikut"
            )
            bot.send_photo(call.message.chat.id,
                           photo=open('./example.jpg', 'rb'))


@bot.message_handler(content_types=['photo'])
def photo(message):
    global user_data
    # get file path
    user = user_data[str(
        message.from_user.id)]  #get unique user id and its data

    if (user['bot_state'] == "beli" and user['buy_state'] == 'size'):
        bot.reply_to(message, "Mohon Tunggu Sebentar ya kak...")
        fileID = message.photo[-1].file_id
        file_info = bot.get_file(fileID)
        path_file = 'https://api.telegram.org/file/bot{0}/{1}'.format(
            API_KEY, file_info.file_path)

        # add image
        oimg = imread(path_file)

        # Preprocessing
        result = process_image(oimg)
        result = "%.2f" % result
        # output
        print("feet size (cm): ", result)
        bot.reply_to(message, "ukuran kaki kamu " + str(result) + " cm")
        #reset state
        resetUser(message.from_user.id)
    else:
        bot.reply_to(
            message,
            "Maaf kak, kakak bisa pesen dulu sepatunya, coba kirim chat 'Mau Beli Sepatu !'"
        )


bot.polling()
