import nltk
from nltk.stem import WordNetLemmatizer
import re
import pickle
import numpy as np
from tensorflow.keras.models import load_model
import json
import random
from datetime import datetime

# datetime object containing current date and time
now = datetime.now()

print("now =", now)

# dd/mm/YY H:M:S
dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
print("date and time =", dt_string)


#the lemmatizer used for trainning
lemmatizer = WordNetLemmatizer()

#loading the trained model
model = load_model('chatbot_model.h5')

# load the data
intents = json.loads(open('intents.json').read())
words = pickle.load(open('words.pkl', 'rb'))
classes = pickle.load(open('classes.pkl', 'rb'))


translate_day = {"Monday":"Lundi", "Tuesday":"Mardi", "Wednesday": "Mercredi", "Thursday": "Jeudi", "Friday": "Vendredi"}

next_day = { "Monday":"Tuesday", "Tuesday":"Wednesday", "Wednesday":"Thursday", "Thursday":"Friday", "Friday":"Monday", "Saturday": "Monday", "Sunday":"Monday" }
list_impr = []

months_31 = [1,3,5,7,8,10,12]

def get_time():
    """
    get the time of the day in seconds
    """
    now = datetime.now()
    time = now.strftime("%H:%M:%S")
    time = time.split(':')
    int_time = int(time[0]) * 60 * 60 + int(time[1]) * 60 + int(time[2])
    return int_time

def get_today():
    """
    get the day (d/m/Y)
    """
    now = datetime.now()
    today = now.strftime("%d/%m/%Y")
    today = today.split("/")
    for i in range(3):
        today[i] = int(today[i])
    name = now.strftime("%A")
    return name,today


class impression(object):
    """a class that describes a valid impression request"""

    def __init__(self, doc_name,n_pages, start_time, date, date_name ):

        #string
        self.doc_name = doc_name

        #int
        self.n_pages = n_pages

        #int (seconds of the day)
        self.start_time = start_time

        #list of 3 ints
        self.date = date

        #string
        self.date_name = date_name

        #string
        self.state = "en attente"

    def get_finish_time(self):
        finish_time = self.n_pages + self.start_time
        finish_date = [self.date_name,self.date]
        if finish_time+1 > 18*3600:
            finish_time = finish_time - 18*3600 +8*3600
            if finish_date[0] == "Friday":
                finish_date[0] = "Monday"
                finish_date[1][0] += 3

        return finish_date[0],finish_date[1], finish_time+1


    def update_state(self):
        """
        updates the state according to th actual time
        """
        _,today = get_today()
        time = get_time()
        if today == self.date  and  time >= self.start_time  and  time <= (self.start_time + self.n_pages):
            self.state = "en cours"
        elif today[2] > self.date[2]:
            self.state = "passe"
        elif today[2] == self.date[2]  and  today[1] > self.date[1]:
            self.state =  "passe"
        elif today[2] == self.date[2]  and  today[1] == self.date[1]  and  today[0] > self.date[0]:
            self.state = "passe"
        elif today == self.date  and (self.start_time + self.n_pages)<time:
            self.state = "passe"
        else:
            self.state = "en attente"

    def fix_date(self):
        """
        fix dates to make sure dates are always in the format x/y/z

        with  x <=30 or 31 or 28 or 29 (depending on the year and the day)
        and   y <= 12
        """
        if self.date[1] in months_31  and  self.date[0] > 31:
            if self.date[1] == 12:
                self.date[0] = date[0] - 31
                self.date[1] = 1
                self.date[2] += 1
            else:
                self.date[0] = 1
                self.date[1] +=1

        elif self.date[1] == 2:
            if self.date[2] % 4 == 0  and  self.date[0] > 29:
                self.date[0] = date[0] - 29
                self.date[1] += 1
            elif self.date[0] > 28:
                self.date[0] = date[0] - 28

        elif self.date[0] > 30:
            self.date[0] = date[0] - 30
            self.date[1] += 1

    def get_str_format(self):
        """
        the string that describes the print request state
        """

        return "Impression de " + self.doc_name + ": " + str(self.n_pages) + "pages\n" + "    etat:" + self.state + "\n    debut impression:" +translate_day[self.date_name]+ " " + str(self.date[0]) + "/" + str(self.date[1])+ "/" +str(self.date[2]) + "\n    à l'heure:" + str(self.start_time//3600)+":"+str((self.start_time%3600)//60) + ":" + str((self.start_time%3600)%60) +"\n\n"



def clean_up_sentence(sentence):
    # tokenize the pattern - splitting words into array
    sentence_words = nltk.word_tokenize(sentence)
    # stemming every word - reducing to base form
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words


# return bag of words array: 0 or 1 for words that exist in sentence
def bag_of_words(sentence, words, show_details=True):
    # tokenizing patterns
    sentence_words = clean_up_sentence(sentence)
    # bag of words - vocabulary matrix
    bag = [0] * len(words)
    for s in sentence_words:
        for i, word in enumerate(words):
            if word == s:
                # assign 1 if current word is in the vocabulary position
                bag[i] = 1
                if show_details:
                    print("found in bag: %s" % word)
    return (np.array(bag))


def predict_class(sentence):
    # filter below  threshold predictions
    p = bag_of_words(sentence, words, show_details=False)
    res = model.predict(np.array([p]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    # sorting strength probability
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    return return_list


def getResponse(ints, intents_json):
    tag = ints[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if (i['tag'] == tag):
            result = random.choice(i['responses'])
            break
    return result


# Creating tkinter GUI
from tkinter import *

import webbrowser
list_impr=[]
def openAgenda():
    new = 2 # open in a new tab, if possible
    #open an HTML file on own computer
    url = "schedule.html"
    webbrowser.open(url,new=new)


# function to open a new window on a button click
def openNewWindow():
    # Toplevel object which will
    # be treated as a new window
    newWindow = Toplevel(root)

    # sets the title of the
    # Toplevel widget
    newWindow.title("Agenda")

    # sets the geometry of toplevel
    newWindow.geometry("700x800")
    newWindow.configure(bg="white")

    # A Label widget to show in toplevel
    Label(newWindow,
          text="Agenda des impressions", bg="white").pack()
    return newWindow


def add_impr_to_list(L, doc_name, nb_pages):
    if (len(L) == 0):
        name,today = get_today()

        if name == "Saturday":
            impr = impression(doc_name, nb_pages, 8*3600, [today[0] + 2, today[1] , today[2]], "Monday")
        elif name == "Sunday":
            impr = impression(doc_name, nb_pages, 8*3600, [today[0] + 1, today[1] , today[2]], "Monday")

        else:
            time = get_time()
            if time>=8*3600 and time <= 18*3600:
                impr = impression(doc_name, nb_pages, time, [today[0] , today[1] , today[2]], name)
            elif time<8*3600:
                impr = impression(doc_name, nb_pages, 8*3600, [today[0] , today[1] , today[2]], name)
            else:
                impr = impression(doc_name, nb_pages, 8*3600, [today[0]+1 , today[1] , today[2]], next_day[name])
    else:
        duree = nb_pages
        for i in range( len(L)):
            L[i].update_state()
        if L[-1].state == "passe":
            name,today = get_today()

            if name == "Saturday":
                impr = impression(doc_name, nb_pages, 8*3600, [today[0] + 2, today[1] , today[2]], "Monday")
                impr.fix_date()
            elif name == "Sunday":
                impr = impression(doc_name, nb_pages, 8*3600, [today[0] + 1, today[1] , today[2]], "Monday")

            else:
                time = get_time()
                if time>=8*3600 and time <= 18*3600:
                    impr = impression(doc_name, nb_pages, time, [today[0] , today[1] , today[2]], name)
                elif time<8*3600:
                    impr = impression(doc_name, nb_pages, 8*3600, [today[0] , today[1] , today[2]], name)
                else:
                    impr = impression(doc_name, nb_pages, 8*3600, [today[0]+1 , today[1] , today[2]], next_day[name])
        else:
            finish_date_name, finish_date, finish_time = L[-1].get_finish_time()
            impr = impression(doc_name, nb_pages, finish_time, finish_date, finish_date_name)
    impr.fix_date()
    impr.update_state()
    L.append(impr)

def send():
    global list_impr
    msg = EntryBox.get("1.0", 'end-1c').strip()
    EntryBox.delete("0.0", END)
    if msg != '':
        ChatBox.config(state=NORMAL)
        ChatBox.insert(END, "Vous: " + msg + '\n\n')
        ChatBox.config(foreground="#f0fafa", font=("Verdana", 12))

        ints = predict_class(msg)
        res = getResponse(ints, intents)

        doc = re.search('doc[0-9]*', msg)
        nb_pages = re.search('\s+[0-9]+\s*', msg)
        new_impri="impression"
        # Action à faire pour l'affichage de créneaux: ouvrir une new fenetre
        if ints[0]['intent'] == 'creneaux':
            ChatBox.insert(END, "PrintBot: " + res + '\n\n')
            # openAgenda() #on a html file opened in browser
            Agenda_window = openNewWindow()
            List_impr_box=Text(Agenda_window, height="1000", width="1000", font="Arial", bg="white", bd=0)
            impressions = []
            idx =-1
            for i in range(len(list_impr)):
                list_impr[i].update_state()
                list_impr[i].fix_date()
                if list_impr[i].state == "passe":
                    idx+=1
            if idx>=0:
                list_impr=list_impr[idx:]
            for i in range(len(list_impr)):
                impressions.append( list_impr[i].get_str_format())
            for i in range(len(impressions)):
                print(impressions[i])
                List_impr_box.insert(END,impressions[i])
            List_impr_box.place(x=50, y=50, height=800, width=800)

        # Action à faire en impression: ajouter le document sur la liste des impressions
        elif ints[0]['intent'] == 'impression':
            no_doc_pages= "Veuillez bien spécifier le nom du document par \"doc\" suivi du numéro du document" \
                    " ainsi que le nombre de pages."

            if (doc == None):
                ChatBox.insert(END, "PrintBot: " + no_doc_pages + '\n\n')
            elif (nb_pages== None):
                ChatBox.insert(END, "PrintBot: " + no_doc_pages + '\n\n')
            else:

                ChatBox.insert(END, "PrintBot: " + res + '\n\n')
                add_impr_to_list(list_impr, doc.group(0), int(nb_pages.group(0)))


        else:
            ChatBox.insert(END, "PrintBot: " + res + '\n\n')

        ChatBox.config(state=DISABLED)
        ChatBox.yview(END)


#=================================================================
#Creating GUI window for chat
#=================================================================
root = Tk()
root.title("Printer Chatbot")
root.geometry("400x500")
root.resizable(width=FALSE, height=FALSE)


# Create Chat window
ChatBox = Text(root, bd=1, bg="black", height="8", width="50", font="Arial", )
ChatBox.config(state=DISABLED)

# Bind scrollbar to Chat window
scrollbar = Scrollbar(root, command=ChatBox.yview, cursor="heart")
ChatBox['yscrollcommand'] = scrollbar.set

# Create Button to send message
SendButton = Button(root, font=("Verdana", 13), text="Envoyer", width="12", height=5,
                    bd=1, bg="light blue", activebackground="#3c9d9b", fg='#000000',
                    command=send)

# Create the box to enter message
EntryBox = Text(root, bd=1, bg="white", width="29", height="5", font="Arial")
# EntryBox.bind("<Return>", send)


# Place all components on the screen
scrollbar.place(x=376, y=6, height=386)
ChatBox.place(x=6, y=6, height=386, width=370)
EntryBox.place(x=6, y=401, height=90, width=265)
SendButton.place(x=222, y=401, height=90)

root.mainloop()

#=================================================================
#Creating GUI window for Timetable
#=================================================================