# INCLUDE

from calendar import week
from tkinter import *
from tkinter import ttk
import numpy as np
import agenda

# INTERFACE

def print_agenda() :


    def couleur(i):
        liste_couleur = ['red', 'green', 'yellow', 'blue', 'black']
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
            lst = np.transpose(cal.get_week(week))
            print(lst)
            documents_print = cal.get_docs(week)

            # nombre lignes et colonnes tableau affiché
            total_rows = len(lst) + 1
            total_columns = len(lst[0]) + 1
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
                        indice = int(lst[i-2][j-2])

                        self.e = Entry(gui, width=10, fg=couleur(indice),
                                   font=('Arial', 10, 'bold'))

                        self.e.grid(row=i, column=j)

                        if indice == 0:
                            self.e.insert(END, ' ')

                        else:
                            self.e.insert(END, documents_print[indice-1])


    gui = Tk()
    t = Table(gui, week)
    gui.mainloop()



