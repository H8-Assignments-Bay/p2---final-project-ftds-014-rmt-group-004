# import library
import string 
import numpy as np
import pickle
from util import JSONParser
from sklearn.pipeline import make_pipeline
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import CountVectorizer
def  preprocess(chat):
    # lowercase transform
    chat = chat.lower()
    tandabaca = tuple(string.punctuation)
    chat = "".join(ch for ch in chat if ch not in tandabaca)
    return chat

# load data 
path = "data/intents.json"
jp = JSONParser()
jp.parse(path)
df=jp.get_dataframe()

# preprocess data 

# case folding transform data into lower case
df['text_input_prep'] = df.text_input.apply(preprocess)

# Modelling 
pipeline = make_pipeline(CountVectorizer(),MultinomialNB())

# train 
print("[INFO] Training....")
pipeline.fit(df.text_input_prep,df.intents)

with open("model_chatbot.pkl", "wb") as model_file:
    pickle.dump(pipeline,model_file)

# def bot_response(chat,pipe,jp):
#     chat = preprocess(chat)
#     res = pipeline.predict_proba([chat])
#     max_prob = max(res[0])
#     if max_prob < .2:
#         return "Maaf kak bisa Diperjelas lagi ngga kak masalahnya ? \n\
#                 saya kurang paham :(",None
#     else:
#         max_id = np.argmax(res[0])
#         pred_tag = pipe.classes_[max_id]
#         return jp.get_response(pred_tag),pred_tag

# # interaction with bot
# print("admin sudah connect")

# while(True):
#     chat = input("Anda >> ")
#     res,tag = bot_response(chat,pipeline,jp)
#     print(f"Admin >> {res}")
#     if tag == 'bye':
#         break

