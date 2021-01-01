import tkinter as tkin
class input_canvas():
    def __init__(self,master):
        self.input_gui = master
        self.canvas1 = tkin.Canvas(self.input_gui, width=400, height=300)

        #Creating entry boxes
        self.entry1 = tkin.Entry(self.input_gui)
        self.entry2 = tkin.Entry(self.input_gui)
        self.entry3 = tkin.Entry(self.input_gui)

    def add_labels(self, label_1,label_2,label_3):
        self.label1 = tkin.Label(self.input_gui, text=label_1)
        self.label2 = tkin.Label(self.input_gui, text=label_2)
        self.label3 = tkin.Label(self.input_gui, text=label_3)

    def setup_grid(self):
    # Specifying locations of entry boxes in grid
        self.entry1.grid(row=0, column=1, pady=5)  # Add pad x ?
        self.entry2.grid(row=2, column=1, pady=5)
        self.entry3.grid(row=4, column=1, pady=5)

    # Specifying locations of labels in grid
        self.label1.grid(row=0, column=0, pady=5, padx=2)
        self.label2.grid(row=2, column=0, pady=5, padx=2)
        self.label3.grid(row=4, column=0, pady=5, padx=2)
    def add_choice_buttons(self, list_of_names):
        pass









#button1 = tkin.Button(text='Get the Square Root', command=getSquareRoot)
#canvas1.create_window(200, 180, window=button1)
input_gui = tkin.Tk()
first_gui = input_canvas(input_gui)
input_gui.mainloop()