from skimage.io import imread,imsave
import telebot
import pickle
from util import JSONParser
import string
import numpy as np

from scipy import ndimage
from imutils import contours
import argparse
import imutils
import cv2

from sklearn.cluster import KMeans
import random as rng


#load model
with open('model/model_chatbot.pkl', 'rb') as handle:
    model = pickle.load(handle)

API_KEY = "5694590247:AAEDwug01HoBKJOrkFrXfi1_Klo7DAXeNPs"
bot = telebot.TeleBot(API_KEY)

""" this is data preprocessing image line


"""

#data preprocess
def preprocess_img(img):

    img = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)

    img = cv2.GaussianBlur(img, (9, 9), 0)
    img = img/255

    return img

# crop image
def cropOrig(bRect, oimg):
    # x (Horizontal), y (Vertical Downwards) are start coordinates
    # img.shape[0] = height of image
    # img.shape[1] = width of image

    x,y,w,h = bRect

    print(x,y,w,h)
    pcropedImg = oimg[y:y+h,x:x+w]

    x1, y1, w1, h1 = 0, 0, pcropedImg.shape[1], pcropedImg.shape[0]

    y2 = int(h1/10)

    x2 = int(w1/10)

    crop1 = pcropedImg[y1+y2:h1-y2,x1+x2:w1-x2]

    #cv2_imshow(crop1)

    ix, iy, iw, ih = x+x2, y+y2, crop1.shape[1], crop1.shape[0]

    croppedImg = oimg[iy:iy+ih,ix:ix+iw]

    return croppedImg, pcropedImg

# overlay Image
def overlayImage(croppedImg, pcropedImg):


    x1, y1, w1, h1 = 0, 0, pcropedImg.shape[1], pcropedImg.shape[0]

    y2 = int(h1/10)

    x2 = int(w1/10)

    new_image = np.zeros((pcropedImg.shape[0], pcropedImg.shape[1], 3), np.uint8)
    new_image[:, 0:pcropedImg.shape[1]] = (255, 0, 0) # (B, G, R)

    new_image[ y1+y2:y1+y2+croppedImg.shape[0], x1+x2:x1+x2+croppedImg.shape[1]] = croppedImg

    return new_image

    
def kMeans_cluster(img):

    # For clustering the image using k-means, we first need to convert it into a 2-dimensional array
    # (H*W, N) N is channel = 3
    image_2D = img.reshape(img.shape[0]*img.shape[1], img.shape[2])

    # tweak the cluster size and see what happens to the Output
    kmeans = KMeans(n_clusters=2, random_state=0).fit(image_2D)
    clustOut = kmeans.cluster_centers_[kmeans.labels_]

    # Reshape back the image from 2D to 3D image
    clustered_3D = clustOut.reshape(img.shape[0], img.shape[1], img.shape[2])

    clusteredImg = np.uint8(clustered_3D*255)

    return clusteredImg

def drawCnt(bRect, contours, cntPoly, img):

    drawing = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint8)   


    paperbb = bRect

    for i in range(len(contours)):
      color = (rng.randint(0,256), rng.randint(0,256), rng.randint(0,256))
      cv2.drawContours(drawing, cntPoly, i, color)
      #cv2.rectangle(drawing, (int(boundRect[i][0]), int(boundRect[i][1])), \
              #(int(boundRect[i][0]+boundRect[i][2]), int(boundRect[i][1]+boundRect[i][3])), color, 2)
    cv2.rectangle(drawing, (int(paperbb[0]), int(paperbb[1])), \
              (int(paperbb[0]+paperbb[2]), int(paperbb[1]+paperbb[3])), color, 2)
    
    return drawing

def edgeDetection(clusteredImage):
  #gray = cv2.cvtColor(hsvImage, cv2.COLOR_BGR2GRAY)
  edged1 = cv2.Canny(clusteredImage, 0, 255)
  edged = cv2.dilate(edged1, None, iterations=1)
  edged = cv2.erode(edged, None, iterations=1)
  return edged

def getBoundingBox(img):

    contours, _ = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    #print(len(contours))
    contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)
    
    

    contours_poly = [None]*len(contours)
    boundRect = [None]*len(contours)

    for i, c in enumerate(contours):
        contours_poly[i] = cv2.approxPolyDP(c, 3, True)
        boundRect[i] = cv2.boundingRect(contours_poly[i])

    return boundRect, contours, contours_poly, img
""" Data Preprocessing ends here """

"""This is printing result"""
def calcFeetSize(pcropedImg, fboundRect):
  x1, y1, w1, h1 = 0, 0, pcropedImg.shape[1], pcropedImg.shape[0]

  y2 = int(h1/10)

  x2 = int(w1/10)

  fh = y2 + fboundRect[2][3]
  fw = x2 + fboundRect[2][2]
  ph = pcropedImg.shape[0]
  pw = pcropedImg.shape[1]

#   print("Feet height: ", fh)
#   print("Feet Width: ", fw)

#   print("Paper height: ", ph)
#   print("Paper Width: ", pw)

  opw = 210
  oph = 297

  ofs = 0.0

  if fw>fh:
    ofs = (oph/pw)*fw
  else :
    ofs = (oph/ph)*fh

  return ofs


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

def bot_response(chat,pipe,jp):
    chat = preprocess(chat)
    res = pipe.predict_proba([chat])
    max_prob = max(res[0])
    if max_prob < .2:
        return "Maaf kak bisa Diperjelas lagi ngga kak masalahnya ? \n\
                saya kurang paham :(",None
    else:
        max_id = np.argmax(res[0])
        pred_tag = pipe.classes_[max_id]
        return jp.get_response(pred_tag),pred_tag


@bot.message_handler(regexp='[a-z]+')
def greet(message):
    print(message.text)
    bot.reply_to(message,bot_response(message.text,model,jp))

@bot.message_handler(content_types=['photo'])
def photo(message):   
    fileID = message.photo[-1].file_id   
    file_info = bot.get_file(fileID)
    file = 'https://api.telegram.org/file/bot{0}/{1}'.format(API_KEY, file_info.file_path)

    oimg = imread(file)
#  downloaded_file = bot.download_file(file_info.file_path)
#  print(downloaded_file)
    # Preprocessing
    pre_img = preprocess_img(oimg)
    clusteredImg = kMeans_cluster(pre_img)
    edgedImg = edgeDetection(clusteredImg)
    boundRect, contours, contours_poly, img = getBoundingBox(edgedImg)
    croppedImg, pcropedImg = cropOrig(boundRect[1], clusteredImg)
    newImg = overlayImage(croppedImg, pcropedImg)
    fedged = edgeDetection(newImg)
    fboundRect, fcnt, fcntpoly, fimg = getBoundingBox(fedged)
    print("feet size (cm): ", calcFeetSize(pcropedImg, fboundRect)/10)

bot.polling()