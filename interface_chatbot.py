import re
import pickle
import numpy as np
from tensorflow import keras
import json
import random
from datetime import datetime
import agenda
import interface_agenda
import spacy
import train_model
from joblib import load

from sklearn.preprocessing import LabelEncoder

# NLP pipeline used during training
nlp = spacy.load("en_core_web_lg")
# Encoder used on classes during training
label_encoder = load("classes_encoder")
# DATE DU MOMENT ACTUEL
now = datetime.now()

print("now =", now)

# dd/mm/YY H:M:S
dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
print("date and time =", dt_string)

# CHARGER MODELE CHATBOT ENTRAINE
model = load('clf_chatbot')

# CHARGER LES DONNEES
intents = json.loads(open('intents.json').read())
# words = pickle.load(open('words.pkl', 'rb'))
# classes = pickle.load(open('classes.pkl', 'rb'))


translate_day = {"Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi", "Thursday": "Jeudi",
                 "Friday": "Vendredi"}

next_day = {"Monday": "Tuesday", "Tuesday": "Wednesday", "Wednesday": "Thursday", "Thursday": "Friday",
            "Friday": "Monday", "Saturday": "Monday", "Sunday": "Monday"}
list_impr = []

months_31 = [1, 3, 5, 7, 8, 10, 12]


def get_time():
    """
    MOMENT DE LA JOURNEE EN SECONDES
    """
    now = datetime.now()
    time = now.strftime("%H:%M:%S")
    time = time.split(':')
    int_time = int(time[0]) * 60 * 60 + int(time[1]) * 60 + int(time[2])
    return int_time


def get_today():
    """
    OBTENIR LE JOUR (d/m/Y)
    """
    now = datetime.now()
    today = now.strftime("%d/%m/%Y")
    today = today.split("/")
    for i in range(3):
        today[i] = int(today[i])
    name = now.strftime("%A")
    return name, today


class impression(object):
    """UNE CLASSE QUI DECRIT UNE REQUETE D'IMPRESSION CORRECTE"""

    def __init__(self, doc_name, n_pages, start_time, date, date_name):

        # string
        self.doc_name = doc_name

        # int
        self.n_pages = n_pages

        # int (seconds of the day)
        self.start_time = start_time

        # list of 3 ints
        self.date = date

        # string
        self.date_name = date_name

        # string
        self.state = "en attente"

    def get_finish_time(self):
        finish_time = self.n_pages + self.start_time
        finish_date = [self.date_name, self.date]
        if finish_time + 1 > 18 * 3600:
            finish_time = finish_time - 18 * 3600 + 8 * 3600
            if finish_date[0] == "Friday":
                finish_date[0] = "Monday"
                finish_date[1][0] += 3

        return finish_date[0], finish_date[1], finish_time + 1

    def update_state(self):
        """
        MAJ DE L'ETAT SELON MOMENT ACTUEL
        """
        _, today = get_today()
        time = get_time()
        if today == self.date and time >= self.start_time and time <= (self.start_time + self.n_pages):
            self.state = "en cours"
        elif today[2] > self.date[2]:
            self.state = "passe"
        elif today[2] == self.date[2] and today[1] > self.date[1]:
            self.state = "passe"
        elif today[2] == self.date[2] and today[1] == self.date[1] and today[0] > self.date[0]:
            self.state = "passe"
        elif today == self.date and (self.start_time + self.n_pages) < time:
            self.state = "passe"
        else:
            self.state = "en attente"

    def fix_date(self):
        """
        ETRE SUR QUE LES DATES ONT LE FORMAT x/y/z

        AVEC  x <=30 OU 31 OU 28 OU 29 (SELON LE MOIS)
        ET   y <= 12
        """
        if self.date[1] in months_31 and self.date[0] > 31:
            if self.date[1] == 12:
                self.date[0] = self.date[0] - 31
                self.date[1] = 1
                self.date[2] += 1
            else:
                self.date[0] = 1
                self.date[1] += 1

        elif self.date[1] == 2:
            if self.date[2] % 4 == 0 and self.date[0] > 29:
                self.date[0] = self.date[0] - 29
                self.date[1] += 1
            elif self.date[0] > 28:
                self.date[0] = self.date[0] - 28

        elif self.date[0] > 30:
            self.date[0] = self.date[0] - 30
            self.date[1] += 1

    def get_str_format(self):
        """
        CHAINE QUI DECRIT L'ETAT DE LA REQUETE D'IMPRESSION
        """

        return "Impression de " + self.doc_name + ": " + str(
            self.n_pages) + "pages\n" + "    etat:" + self.state + "\n    debut impression:" + translate_day[
                   self.date_name] + " " + str(self.date[0]) + "/" + str(self.date[1]) + "/" + str(
            self.date[2]) + "\n    à l'heure:" + str(self.start_time // 3600) + ":" + str(
            (self.start_time % 3600) // 60) + ":" + str((self.start_time % 3600) % 60) + "\n\n"


def predict_class(sentence):
    sentence_embedded = train_model.process_text(sentence, preprocessed=False, mode="embed")
    sentence_averaged = (np.mean(sentence_embedded, axis=0)).reshape(1, -1)
    y_pred = model.predict(sentence_averaged)
    print(y_pred)
    return y_pred[0]


def getResponse(tag, intents_json):
    for intent in intents['intents']:
        if intent['tag'] == tag:
            result = random.choice(intent['responses'])
            break
    if result is None:
        raise ValueError("Predicted class not found in answers dataset")
    return result


# FENETRE
from tkinter import *


# NOUVELLE FENETRE AVEC CLIC DE BOUTON
def openNewWindow():
    root.destroy()
    interface_agenda.print_agenda()

def send():
    global list_impr
    msg = EntryBox.get("1.0", 'end-1c').strip()
    EntryBox.delete("0.0", END)
    calendar = agenda.Calendar("calendar")
    if msg != '':
        ChatBox.config(state=NORMAL)
        ChatBox.insert(END, "Vous: " + msg + '\n\n')
        ChatBox.config(foreground="#f0fafa", font=("Verdana", 12))

        intent_tag = predict_class(msg)
        answer = getResponse(intent_tag, intents)

        new_impri = "impression"
        if intent_tag == 'check_schedule':
            ChatBox.insert(END, "PrintBot: " + answer + '\n\n')
            Agenda_window = openNewWindow()

        elif intent_tag == 'printing_request':
            print("PRINTINGGGG")
            no_doc_pages = "Please make sure to input the document name and its file extension, along with the number " \
                           "of pages, and ONLY that number. "
            number_found = 0
            nb_pages = ""
            for word in nlp(msg).ents:
                if word.label_ == "CARDINAL":
                    number_found += 1
                    nb_pages = word.text
                    
            doc = re.search("\w+\.(doc|docx|odf|pdf|jpg|png|jpeg|svg)", msg).group(0)

            if doc is None or nb_pages == "":
                ChatBox.insert(END, "PrintBot: " + no_doc_pages + '\n\n')
            else:

                ChatBox.insert(END, "PrintBot: " + answer + '\n\n')
                calendar.add_document(doc.group(0), int(nb_pages.group(0)))

        else:
            ChatBox.insert(END, "PrintBot: " + answer + '\n\n')

        ChatBox.config(state=DISABLED)
        ChatBox.yview(END)


# FENETRE POUR LE CHATBOT
root = Tk()
root.title("Printer Chatbot")
root.geometry("450x500")
root.resizable(width=FALSE, height=FALSE)

# FENETRE DE CHAT
ChatBox = Text(root, bd=1, bg="black", height="8", width="50", font="Arial", )
ChatBox.config(state=DISABLED)

# Bind scrollbar to Chat window
scrollbar = Scrollbar(root, command=ChatBox.yview, cursor="heart")
ChatBox['yscrollcommand'] = scrollbar.set

# BOUTON POUR ENVOYER MESSAGES
SendButton = Button(root, font=("Verdana", 13), text="Envoyer", width="10", height=3,
                    bd=1, bg="light blue", activebackground="#3c9d9b", fg='#000000',
                    command=send)

# BOX ENTREE MESSAGE
EntryBox = Text(root, bd=1, bg="white", width="20", height="5", font="Arial")
# EntryBox.bind("<Return>", send)


# PLACE DES COMPOSANTS SUR L'ECRAN
scrollbar.place(x=376, y=6, height=386)
ChatBox.place(x=6, y=6, height=386, width=370)
EntryBox.place(x=6, y=401, height=90, width=310)
SendButton.place(x=322, y=401, height=90)

root.mainloop()
