from skimage.io import imread
import telebot
import pickle

import string
import numpy as np

from util import JSONParser
from util import process_image


bot_state = None

#load model
with open('model/model_chatbot.pkl', 'rb') as handle:
    model = pickle.load(handle)

API_KEY = "5694590247:AAEDwug01HoBKJOrkFrXfi1_Klo7DAXeNPs"
bot = telebot.TeleBot(API_KEY)

# load data 
path = "data/intents.json"
jp = JSONParser()
jp.parse(path)
df=jp.get_dataframe()

def  preprocess(chat):
    # lowercase transform
    chat = chat.lower()
    tandabaca = tuple(string.punctuation)
    chat = "".join(ch for ch in chat if ch not in tandabaca)
    return chat

def update_state(chat,pipe):
    chat = preprocess(chat)
    res = pipe.predict_proba([chat])
    max_prob = max(res[0])
    if max_prob < .2:
        return "error"
    else:
        max_id = np.argmax(res[0])
        pred_tag = pipe.classes_[max_id]
        return pred_tag
    
    
def bot_response(bot_state,jp):
    if bot_state == "error":
        return "Maaf kak bisa Diperjelas lagi ngga kak masalahnya ? \n\
        saya kurang paham :(",None
    else:
        return jp.get_response(bot_state),bot_state


@bot.message_handler(regexp='[a-z]+')
def greet(message):
    bot_state = update_state(message.text,model)
    print(message.text)
    bot.reply_to(message,bot_response(bot_state,jp))

@bot.message_handler(content_types=['photo'])
def photo(message):
    
    # get file path
    fileID = message.photo[-1].file_id   
    file_info = bot.get_file(fileID)
    path_file = 'https://api.telegram.org/file/bot{0}/{1}'.format(API_KEY, file_info.file_path)
    
    # add image
    oimg = imread(path_file)

    # Preprocessing
    result = process_image(oimg)
    # output nya
    print("feet size (cm): ", result)
    bot.reply_to(message, "ukuran kaki kamu "+str(result)+" cm")

bot.polling()