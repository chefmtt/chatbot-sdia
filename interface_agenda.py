# INCLUDE

from calendar import week
from tkinter import *
from tkinter import ttk
import numpy as np
import agenda

# INTERFACE

# def print_agenda() :

def couleur(i):
    liste_couleur = ['red', 'green', 'yellow', 'blue', 'black', 'orange', 'pink']
    return liste_couleur[i]


def callback1():
    global week
    week = 45
    gui.destroy()


def callback2():
    global week
    week = 46
    gui.destroy()


def callback3():
    global week
    week = 47
    gui.destroy()


gui = Tk()
v = IntVar
gui.geometry('200x100')
btn1 = Button(gui, text="45", command=callback1)
btn1.pack()
btn2 = Button(gui, text="46", command=callback2)
btn2.pack()
btn3 = Button(gui, text="47", command=callback3)
btn3.pack()
gui.mainloop()

# tableau qui affiche les données
class Table:

    def __init__(self, gui, week):

        # données utilisées
        cal = agenda.Calendar("calendar")
        # dimension 1440x7
        lst = np.ones((1440, 7))
        print(len(lst))
        documents_print = cal.get_docs(week)

        # nombre lignes (horaires) et colonnes (jours) tableau affiché
        total_rows = 25
        total_columns = 8
        print(total_rows)
        print(total_columns)

        list_jours = ['Lundi', 'Mardi', 'Mercredi',
                        'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']

        # code pour créer la table
        for i in range(total_rows):
            for j in range(total_columns):

                if i == 0:
                    if j != 0:
                        self.e = Entry(gui, width=10, fg='blue',
                                        font=('Arial', 10, 'bold'))

                        self.e.grid(row=i, column=j)
                        self.e.insert(END, list_jours[j-1])
                    else:
                        self.e = Entry(gui, width=10, fg='black',
                                        font=('Arial', 10))

                        self.e.grid(row=i, column=j)
                        self.e.insert(END, 'Horaire')

                elif j == 0:
                    if i != 0:
                        self.e = Entry(gui, width=10, fg='blue',
                                        font=('Arial', 10, 'bold'))

                        self.e.grid(row=i, column=j)
                        self.e.insert(END, str(i-1) + ':00')

                else:
                    for minute in range(60) :
                        indice_minute = i + minute - 2
                        indice = int(lst[indice_minute][j-2])

                        self.e = Entry(gui, width=10, fg=couleur(indice-1),
                                        font=('Arial', 10, 'bold'))

                        self.e.grid(row=i, column=j)

                        if indice == 0:
                            self.e.insert(END, ' ')

                        else:
                            self.e.insert(END, '■')


gui = Tk()
t = Table(gui, week)
gui.mainloop()



