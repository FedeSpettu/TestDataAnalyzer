import tkinter as tk
from tkinter import Tk, Checkbutton, Button, Scrollbar, messagebox
import customtkinter as ctk
import os.path
# Tkinter GUI code
ctk.set_appearance_mode('Dark')
ctk.set_default_color_theme("dark-blue")

root2 = ctk.CTk()
screen_width = root2.winfo_screenwidth()
screen_height = root2.winfo_screenheight()
root2.overrideredirect(True)
# Set the position of the root window to the center of the screen.
root2.geometry(f"+{screen_width // 2 - root2.winfo_width() // 2}+{screen_height // 2 - root2.winfo_height() // 2}")
root2.resizable(width=False, height=False)
root2.grid_columnconfigure(0, weight=0)
root2.title("Test Data Analyzer")
 
#root2.withdraw() 
checkbox_vars = []
checkboxes = []
selected = []
files=[]

def create_gui(folder_path, files_input):
   try:
      if os.path.isfile('options.txt'):
         os.remove('options.txt')
      if os.path.isfile('options1.txt'):
         os.remove('options1.txt')
      if os.path.isfile('options2.txt'):
         os.remove('options2.txt')
      if os.path.isfile('output0.csv'):
         os.remove('output0.csv')
      if os.path.isfile('output1.csv'):
         os.remove('output1.csv')
      if os.path.isfile('options.txt'):
         os.remove('options.txt')
      if os.path.isfile('check.csv'):
         os.remove('check.csv')
      if os.path.isfile('data.csv'):
         os.remove('data.csv')
      if os.path.isfile('backup.csv'):
         os.remove('backup.csv')
      if os.path.isfile('backupdf2.csv'):
         os.remove('backupdf2.csv')
      if os.path.isfile('backupprova.csv'):    
         os.remove('backupprova.csv')
      if os.path.isfile('prova2.csv'):
         os.remove('prova2.csv')
      if os.path.isfile('plot.png'):    
         os.remove('plot.png')
      global checkboxes
      global checkbox_vars
      global selected
      global files
      checkbox_vars = []
      checkboxes = []
      selected = []
      files=[]
      root2.deiconify()
      frame = ctk.CTkFrame(root2)
      frame.grid(row=0, column=0, sticky="nws") 
      
      canvas = ctk.CTkCanvas(frame, width=500, height=200)
      canvas.grid(row=0, column=0, sticky="nws") 
      
      scrollbar = ctk.CTkScrollbar(frame, command=canvas.yview)
      scrollbar.grid(row=0, column=1, sticky="ns")

      canvas.configure(yscrollcommand=scrollbar.set, background='black')
      canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all'))) 

      inner_frame = ctk.CTkFrame(canvas)
      canvas.create_window((0, 0), window=inner_frame, anchor='nw')
      files = files_input
      for i, file in enumerate(files):

         var = tk.IntVar()
         checkbox = ctk.CTkCheckBox(inner_frame, text=file, variable=var)
         checkbox.grid(sticky='w')

         checkbox_vars.append(var)
         checkboxes.append(checkbox)
         
      for i in range(len(checkboxes)):
         checkbox_vars[i].set(0)

      box=ctk.CTkFrame(root2)
      box.grid(row=1, column=0)

      select_btn = ctk.CTkButton(box, text="Select All", command=select_all)
      select_btn.grid(row=0,column=0, pady=10)

      clear_btn = ctk.CTkButton(box, text="Clear All", command=clear_all)
      clear_btn.grid(row=1,column=1,pady=10)

      save_btn = ctk.CTkButton(box, text="Save Selected", command=lambda: save(folder_path)) 
      save_btn.grid(row=0,column=2,pady=10)

      confirm_btn = ctk.CTkButton(box, text="Confirm Selection", command=confirm) 
      confirm_btn.grid(row=0,column=1,pady=10)

      btn_quit = ctk.CTkButton(box, text="Quit", command=lambda: quit())
      btn_quit.grid(row=1,column=2,pady=10)

      
      select_btn['state'] = 'normal'
      clear_btn['state'] = 'normal'

      root2.mainloop() 
   except Exception as e:
        root=tk.Tk()
        print(e)
        error_message = e.args
        messagebox.showerror("Critical Error", str(error_message))

def confirm():
   try:
      global files
      global checkbox_vars
      global checkboxes
      global selected
      j=0
      
      selected.clear()
      for i in range(len(checkboxes)):
            if checkbox_vars[i].get()==1 and j < len(files):
               
               selected.append(files[j])
            j+=1
      
   except Exception as e:
        root=tk.Tk()
        print(e)
        error_message = e.args
        messagebox.showerror("Critical Error", str(error_message))

def select_all():
   try:
      global files
      global checkbox_vars
      global checkboxes
      global selected
      for i in range(len(checkboxes)):
         checkbox_vars[i].set(1)

   except Exception as e:
        root=tk.Tk()
        print(e)
        error_message = e.args
        messagebox.showerror("Critical Error", str(error_message))

def quit():
      root2.withdraw()

def clear_all():
   try:
      global files
      global checkbox_vars
      global checkboxes
      global selected
      for i in range(len(checkboxes)):
         checkbox_vars[i].set(0)
      #select_btn['state'] = 'normal'
   except Exception as e:
        root=tk.Tk()
        print(e)
        error_message = e.args
        messagebox.showerror("Critical Error", str(error_message))

      
def save(folder_path):
   global files
   global checkbox_vars
   global checkboxes
   global selected
   with open("interactive_plot.txt", "w") as file:
    pass  # This creates an empty file
   try:
      with open('options.txt', 'w') as f:
         for filename in selected:
            f.write(filename + '\n')
         
      messagebox.showinfo("Done", "The options have been saved", parent=root2)
      
   except Exception as e:
        root=tk.Tk()
        print(e)
        error_message = e.args
        messagebox.showerror("Critical Error", str(error_message))

class ErrorDialog(tk.Toplevel):
    def __init__(self, parent, message, title):
        super().__init__(parent)
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        parent.geometry(f"+{screen_width // 2 - parent.winfo_width() // 2}+{screen_height // 2 - parent.winfo_height() // 2}")
        self.title(title)
        self.message = message

        # crea un'etichetta per il messaggio di errore
        label = tk.Label(self, text=self.message)
        label.pack()

        # crea un pulsante per chiudere la finestra di dialogo
        button = tk.Button(self, text="Close", command=self.destroy)
        button.pack()
