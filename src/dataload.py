import time
import tkinter as tk
from tkinter import ALL, Canvas, filedialog
import os
import re
import pandas as pd
import csv
from datetime import datetime
import openpyxl
import matplotlib
matplotlib.use('TkAgg')
from .global_var import *
from .usefull_functions import is_float, is_datetime, auto_detect_delimiter, remove_special_characters, remove_special_characters_from_list
from PIL import Image, ImageTk, ImageSequence
from src import dataload as dl, selectfoldergui
from tkinter import messagebox as mbox
import sys
from tkinter import Checkbutton, Button, Scrollbar, messagebox
from functools import wraps
import customtkinter as ctk
from src import loading
from src import ScrubDiagnostic as sd
from src import ScrubSniffer as sj
from pathlib import Path

def reset_gui( elements):
    
    global clean_paths 
    clean_paths=[]
    global plot_dictionary
    plot_dictionary= {
    }
    global selection 
    selection = {
        'File1': [],
        'File2': []
    }
    global folder_path
    folder_path=[]
    global output_path
    output_path=''
    global output_file
    output_file=''
    global k
    k=-1
    global z
    z=0
    if os.path.isfile('options_multi.txt'):
        os.remove('options_multi.txt')
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
    if os.path.isfile('prova.csv'):    
        os.remove('prova.csv')
    if os.path.isfile('prova1.csv'):    
        os.remove('prova1.csv')
    if os.path.isfile('prova3.csv'):    
        os.remove('prova3.csv')
    if os.path.isfile('backupdf1.csv'):    
        os.remove('backupdf1.csv')
    if os.path.isfile('backupdoasjfouieqhfiufho.csv'):    
        os.remove('backupdoasjfouieqhfiufho.csv')
    if os.path.isfile('output0check.csv'):    
        os.remove('output0check.csv')
    if os.path.isfile('output1check.csv'):    
        os.remove('output1check.csv')
    if os.path.isfile('options_event.txt'):
        os.remove('options_event.txt')
    global currentpage
    currentpage=0
    global min_data_rows
    min_data_rows = 2 
    if trace_id1:
        elements[5].disable_trace(trace_id1) 
        elements[5].trace_vdelete('w', trace_id1)

    if trace_id:    
        elements[5].disable_trace(trace_id1)
        elements[6].trace_vdelete('w', trace_id)

    for element in elements:
     
        if isinstance(element, tk.Listbox):
            element.delete(0, tk.END)
        
    


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

def clear_all_local_variables():
    if os.path.isfile('options_multi.txt'):
        os.remove('options_multi.txt')
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
    if os.path.isfile('prova.csv'):    
        os.remove('prova.csv')
    if os.path.isfile('prova1.csv'):    
        os.remove('prova1.csv')
    if os.path.isfile('prova3.csv'):    
        os.remove('prova3.csv')
    if os.path.isfile('backupdf1.csv'):    
        os.remove('backupdf1.csv')
    if os.path.isfile('backupdoasjfouieqhfiufho.csv'):    
        os.remove('backupdoasjfouieqhfiufho.csv')
    if os.path.isfile('output0check.csv'):    
        os.remove('output0check.csv')
    if os.path.isfile('output1check.csv'):    
        os.remove('output1check.csv')
    if os.path.isfile('options_event.txt'):
        os.remove('options_event.txt')
    for variable in locals():
        del variable

file_ext=[]

# Identify data rows by checking if values look like numbers/datetime   
def find_data(file):
    try:
        global file_ext
        data_rows = []
        data_rows2 = []
        dat1=0
        file_ext = file.split('.')[-1]
        count_log=0
        with open(file) as f:
            for i, row in enumerate(f):
                    
                    # Check if the row is only a newline character
                    if row.strip() == '' or row.strip() == '\n':
                        continue  # Skip this empty row
                    
                    if '['in row or ']' in row:
                        row=row.replace('[', '').replace(']', '')
                        line_content = list(filter(None, re.split('[ |] ', row)))
                        #print(line_content)
                        first_col = line_content[0]
                        
                        if first_col[0] == '[' and first_col[-1] == ']':
                                first_col = first_col[1:-1]
                                first_col=first_col.split()
                                
                        if first_col[0].isnumeric() or is_float(first_col[0]) or is_datetime(first_col[0]):
                                
                                if not data_rows and i > 0:  # if it is the first added line - add also the previous line which is the header
                                    data_rows.append(i - 1)
                                data_rows.append(i)
                        else:
                                if dat1==0 and len(data_rows)==0:
                                    
                                    dat1=0
                                else:
                                    dat1=1
                    else:
                        line_content = list(filter(None, re.split('[ |] ', row)))
                        first_col = line_content[0]
                        #print(first_col[0])
                        if first_col[0] == '[' and first_col[-1] == ']':
                                first_col = first_col[1:-1]
                        if first_col[0].isnumeric() or is_float(first_col[0] or is_datetime(first_col[0])):
                                if dat1==0:
                                    if not data_rows and i > 0:  # if it is the first added line - add also the previous line which is the header
                                            data_rows.append(i - 1)
                                            
                                    data_rows.append(i)
                                else:
                                    if not data_rows2 and i > 0:  # if it is the first added line - add also the previous line which is the header
                                            data_rows2.append(i - 1)
                                    data_rows2.append(i)
                        else:
                                if dat1==0 and len(data_rows)==0:
                                    
                                    dat1=0
                                else:
                                    dat1=1
            
        if file_ext == 'log':
            data_rows = data_rows[1:]
            data_rows2=data_rows2[1:]
            
        return data_rows, data_rows2
    except Exception as e:
        root=tk.Tk()
        root.withdraw()
        messagebox.showerror("Critical Error", str(e.args))

def load_data_mult(file_path):
    
    try:
        k=0
        global output_path
        directory_path = file_path
        print(directory_path)
        # Regular expression pattern to match 'diagnostic' in a file name
        pattern = re.compile(r'DiagnosticLog', re.IGNORECASE)

        # Iterate through files in the directory
        file_path = folder_path + '\\' + file_path
        file_ext = file_path.split('.')[-1]

        # if pattern.search(directory_path):
        #     output_name=sd.scrub_diagnostic(directory_path)
        #     file_path=output_name
            
        # elif file_ext == 'json':
        #     output_name=sj.scrub_json(directory_path)
        #     file_path=output_name
        output_name=sd.scrub_diagnostic(directory_path)
        if output_name:
            file_path=output_name
           
        if output_name == False:
            output_name=sj.scrub_json(directory_path)
 
        if output_name:  
            file_path=output_name

        elif file_ext == 'xlsx':
            df = pd.read_excel(file_path)
            df.to_csv('data.csv', index=False)
            file_path='data.csv'
            
        keep, keep2 = find_data(directory_path)
        delimiter = auto_detect_delimiter(directory_path)
        pattern = re.compile(delimiter)  # Compila una volta la regex
        with open(directory_path, 'r') as f:
            rows = [pattern.split(line.strip()) for line in f]
            
            data_to_save = [rows[i] for i in sorted(keep)]
            df = pd.DataFrame(data_to_save)
            
            if len(keep2) != 0:
            
                # Read the file content into a variable
                f.seek(0)
                rows = [pattern.split(line.strip()) for line in f]
                
                data_to_save = [rows[i] for i in sorted(keep2)]
                df1 = pd.DataFrame(data_to_save)
            
                df = pd.concat([df, df1], axis=1)

        output='output'+str(k)+'.csv'     
        df.to_csv(output, index=False, header=False)
            
    except Exception as e:
        root=tk.Tk()
        root.withdraw() 
        messagebox.showerror("Critical Error", str(e.args))
    
    #column_selection(output,  drop2, clicked2, file_list2)

# Extract data rows from file 
def load_data(file_path, drop2, clicked2, file_list2, loading_label, root, entry2):
   
    try:
        global output_path
        directory_path = folder_path + '/' + file_path
        print(directory_path)
        
        # Regular expression pattern to match 'diagnostic' in a file name
        pattern = re.compile(r'DiagnosticLog', re.IGNORECASE)
 
        # Iterate through files in the directory
        file_path = folder_path + '\\' + file_path
        file_ext = file_path.split('.')[-1]
 
        output_name, start_time_diagnostic=sd.scrub_diagnostic(directory_path)
        if output_name:
            file_path=output_name
            print("start_time_diagnostic:" ,start_time_diagnostic)
            
           
        if output_name == False:
            output_name, start_time_json=sj.scrub_json(directory_path)
            #print(output_name)
            print("start_time_json:",start_time_json)
            

        if output_name:  
            file_path=output_name
 
        elif file_ext == 'xlsx':
            df = pd.read_excel(file_path)
            df.to_csv('data.csv', index=False)
            file_path='data.csv'

        filename = Path(file_path).name  

        # Validate format
        pattern_file = r"^DataLog_\d{6}_\d{6}"
        if re.match(pattern_file, filename):
            time_part = filename.split("_")[2] 
            start_time_datalog = f"{time_part[:2]}:{time_part[2:4]}:{time_part[4:]}"  # Convert to HH:MM:SS
            print(start_time_datalog)  
        else:
            print("Invalid filename format")

        keep, keep2 = find_data(file_path)
        delimiter = auto_detect_delimiter(file_path)
        pattern = re.compile(delimiter)  # Compila una volta la regex
        files_selection.append(file_path)
        print("File selection:", files_selection)
        with open(file_path, 'r') as f:
            rows = [pattern.split(line.strip()) for line in f]
           
            data_to_save = [rows[i] for i in sorted(keep)]
            df = pd.DataFrame(data_to_save)
           
            if len(keep2) != 0:
           
                # Read the file content into a variable
                f.seek(0)
                rows = [pattern.split(line.strip()) for line in f]
               
                data_to_save = [rows[i] for i in sorted(keep2)]
                df1 = pd.DataFrame(data_to_save)
           
                df = pd.concat([df, df1], axis=1)
        output='output'+str(k)+'.csv' 
        #print(output)
        #print(df.columns)
        
        df.to_csv(output, index=False, header=False)
           
    except Exception as e:
        root=tk.Tk()
        root.withdraw()
        messagebox.showerror("Critical Error", str(e.args))
        loading_label.destroy()
    
    column_selection(output,  drop2, clicked2, file_list2, entry2, loading_label, root, k)

def truncate_text(text, max_length=30):
    """Returns the text truncated to max_length characters (including an ellipsis) if needed."""
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text
# Allow user to pick folder and load files dropdown 
def select_folder(file_list, drop1, drop2, clicked1, clicked2, folder_label, file_list2, entry, entry2):
    
    try:
        global folder_path
        global k
        global files
        global output_path
        k=k+1
        folder_path=[]
        folder_path = filedialog.askdirectory()
        
        if folder_path:
            folder_label.configure(text=truncate_text(folder_path, 25))
            file_list.delete(0, tk.END)  # Pulisce la lista precedente, 
            files = load_files_in_folder(folder_path, file_list)
           
    except Exception as e:
        root=tk.Tk()
        root.withdraw()
        messagebox.showerror("Critical Error", str(e.args))
    update_option_menu(files, drop1, drop2, clicked1, clicked2, file_list2, entry, entry2, file_list)

# Allow selecting Excel output folder 

      
# Update dropdown menus with new options  
def update_option_menu(files1, drop1, drop2, clicked1, clicked2, file_list2, entry, entry2, file_list):
    try:
        global files
        drop1["menu"].delete(0, "end")

        search_term = entry.get().lower()
       
        # Populate menu with filtered options
        for file_name in files:
            if search_term in file_name.lower():
                drop1["menu"].add_command(
                    label=file_name,
                    command=lambda value=file_name: load_file(drop1, drop2, value, clicked2, file_list2, clicked1, entry2, file_list)
                )
               
        #clicked1.set(files[0])
    except Exception as e:
        root=tk.Tk()
        root.withdraw()
        messagebox.showerror("Critical Error", str(e.args))

timer_id = None
import threading
import queue


class LoadingScreen:
    def __init__(self, root, value, drop2, clicked2, file_list2, entry2):
        self.root = root
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.title("Loading columns")
        self.root.geometry(f"+{screen_width // 2 - root.winfo_width() // 2}+{screen_height // 2 - root.winfo_height() // 2}")
        #self.root.geometry("300x330+400+300")  # Set your desired size and position

        self.after_queue = queue.Queue()
        gif_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '', 'giphy.gif')
        self.loading_gif = Image.open(gif_path)
        self.frames = [ImageTk.PhotoImage(frame.copy()) for frame in ImageSequence.Iterator(self.loading_gif)]

        self.loading_label = tk.Label(root)
        self.loading_label.pack()

        self.frame_num = 0
        self.loading = True
        self.load_thread = threading.Thread(target=self.load_big_file, args=(root, value, drop2, clicked2, file_list2, entry2))
        self.load_thread.start()

        self.update_frames()

    def update_frames(self):
        if self.loading_label.winfo_exists():
            self.loading_label.configure(image=self.frames[self.frame_num])
            self.loading_label.image = self.frames[self.frame_num]
            self.loading_label.update()  # Force update

            # Move to the next frame
            self.frame_num = (self.frame_num + 1) % len(self.frames)

        if self.loading:
            self.root.after(1, self.update_frames)  # Adjust the delay as needed

    def load_big_file(self, root, value, drop2, clicked2, file_list2, entry2):
        try:
            while self.loading:
                # Simulate loading a big file (replace this with your actual file loading logic)
                load_data(value, drop2, clicked2, file_list2, self.loading_label, root, entry2)
                self.loading = False
                #time.sleep(0.1)  # Simulate a short delay for demonstration
        except Exception as e:
        
            messagebox.showerror("Critical Error", str(e.args))
          

def loading_fun(value, drop2, clicked2, file_list2, entry2):
    root_load = tk.Toplevel()
    root_load.overrideredirect(True)
    screen_width = root_load.winfo_screenwidth()
    screen_height = root_load.winfo_screenheight()
    root_load.geometry(f"+{screen_width // 2 - 165}+{screen_height // 2 - 165}")
    app = LoadingScreen(root_load, value, drop2, clicked2, file_list2, entry2)
    root_load.mainloop()


# Load selected file and get columns
def load_file(drop1,drop2, value, clicked2, file_list2,clicked1, entry2,file_list, *args):
    
    try:
        
        clicked1.set(value)
        file_list.insert(tk.END, value)
        loading_fun(value, drop2, clicked2, file_list2, entry2)
        
    except Exception as e:
         root=tk.Tk()
         root.withdraw()
         print(e)
         error_message = e.args
         messagebox.showerror("Critical Error", str(e.args))

def remove_spaces_and_replace_with_comma(input_file_path):
    try:
        file_name, file_extension = os.path.splitext(input_file_path)
        output_file_path = f"{file_name}_modified.csv"
        #additional_output_file_path = f"{file_name}.csv"
        with open(input_file_path, 'r', newline='') as infile:
            with open(output_file_path, 'w', newline='') as outfile:#, open(additional_output_file_path, 'w', newline='') as additional_outfile:
                for line in infile:
                    # Remove spaces and replace with a comma
                    line = line.replace(' ', ',')
                    outfile.write(line)
                    #additional_outfile.write(line)

    except Exception as e:
        messagebox.showerror("Critical Error", str(e.args))
        
        
# Load columns headers into dropdown 
def column_selection(path,  drop2, clicked2, file_list2, entry2, loading_label, root, k):
    global checktrace
    global headers
    global file_ext
    if path == "output1.csv":
        # Load the CSV into a DataFrame
        df = pd.read_csv(path, sep=',', encoding='latin-1', engine='python')
        # Check if "Event" column exists and drop it
        if "Event" in df.columns:
            df = df.drop(columns=["Event"]) 
            df.to_csv(path, index=False)
    try:      
        if file_ext == 'log':
            remove_spaces_and_replace_with_comma(path)
           
            file_name, file_extension = os.path.splitext(path)
            output_file_path = f"{file_name}_modified.csv"
            with open(output_file_path, 'r') as f:
                reader = csv.reader(f, delimiter=',')
                headers = next(reader)  # Read the first row (header)

                # If the header row is empty, read the next non-empty row as the header
                while not any(headers):
                    
                    headers = next(reader)
        else:
            
            with open(path, 'r') as f:
                
                reader = csv.reader(f, delimiter=",")
                headers = next(reader)  # Read the first row (header)

                # If the header row is empty, read the next non-empty row as the header
                while not any(headers):
                    
                    headers = next(reader)
      
    except Exception as e:
        remove_spaces_and_replace_with_comma(path)
        file_name, file_extension = os.path.splitext(path)
        output_file_path = f"{file_name}_modified.csv"
        
        with open(output_file_path, 'r') as f:
            reader = csv.reader(f, delimiter=',')
            headers = next(reader)  # Read the first row (header)

            # If the header row is empty, read the next non-empty row as the header
            while not any(headers):
                
                headers = next(reader)
     
    update_option_column(headers, drop2, clicked2, file_list2, entry2, k)
    loading_label.destroy()
    root.withdraw()
    time.sleep(0.2)
    
    messagebox.showinfo("Done", "Columns have been uploaded", parent=root) 
    
    
def update_option_column(first_row, drop, clicked, file_list2, entry2, k):
    try:
        global headers
        # Imposta first_row come headers globali
        first_row = headers

        global trace_id
        trace_id = ''
        # Rimuove caratteri speciali dalla lista
        first_row = remove_special_characters_from_list(first_row)
        for i, element in enumerate(first_row):
            first_row[i] = element.replace('[', '').replace(']', '')

        # Ottieni il termine di ricerca dalla entry e filtra le opzioni
        search_term = entry2.get().lower()
        filtered_options = [file_name for file_name in first_row if search_term in file_name.lower()]

        # Numero di elementi da mostrare per pagina
        ITEMS_PER_PAGE = 20

        def update_menu(page=0, repost=False):
            menu = drop["menu"]
            menu.delete(0, "end")  # Svuota il menu corrente
            start = page * ITEMS_PER_PAGE
            end = start + ITEMS_PER_PAGE
            # Ottieni la fetta corrente delle opzioni filtrate
            current_slice = filtered_options[start:end]
            
            # Aggiungi i comandi per le opzioni della pagina corrente
            for file_name in current_slice:
                menu.add_command(
                    label=file_name,
                    command=lambda value=file_name: updatelist(value, file_list2, k)
                )
            # Se ci sono altre opzioni dopo, aggiungi "More >>"
            if end < len(filtered_options):
                menu.add_command(
                    label="More >>",
                    command=lambda: update_menu(page + 1, repost=True)
                )
            # Se non siamo alla prima pagina, aggiungi "<< Previous"
            if page > 0:
                menu.add_command(
                    label="<< Previous",
                    command=lambda: update_menu(page - 1, repost=True)
                )
            # Se si tratta di una navigazione, riposiziona il menu in modo che rimanga aperto
            if repost:
                x = drop.winfo_rootx()
                y = drop.winfo_rooty() + drop.winfo_height()
                menu.post(x, y)

        # Aggiorna il menu partendo dalla prima pagina (page 0)
        update_menu(page=0)

    except Exception as e:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        print(e)
        messagebox.showerror("Critical Error", str(e.args))
    
        
def updatelist(clicked, file_list2, k, *args):
    try:
        #global k
        global selection
        file_list2.insert(tk.END, clicked)
        if k == 0:
            selection['File1'].append(clicked)
            
        else:
            selection['File2'].append(clicked)
        
        if selection['File1']:
            with open('options1.txt', 'w') as f:
                for filename in selection['File1']:
                    f.write(filename + '\n')
        if selection['File2']:
            with open('options2.txt', 'w') as f:
                for filename in selection['File2']:
                    f.write(filename + '\n')
        
    except Exception as e:
        root=tk.Tk()
        root.withdraw()
        messagebox.showerror("Critical Error", str(e.args))



def create_g():
    try:
        selectfoldergui.create_gui(folder_path, files)
    except Exception as e:
        root=tk.Tk()
        root.withdraw()
        messagebox.showerror("Critical Error", str(e.args))

def load_files_in_folder(folder_path, file_listbox):
    # files = os.listdir(folder_path)
    try:
        files = os.listdir(folder_path) 

        # Get last file created
        files_with_date = [(f, os.path.getctime(os.path.join(folder_path, f))) for f in files]
        last_file = sorted(files_with_date, key=lambda x: x[1])[-1][0]

        # Remove from files list
        files.remove(last_file)
        #for file_name in files:
        #    file_listbox.insert(tk.END, file_name)
        return files
    except Exception as e:
        root=tk.Tk()
        root.withdraw()
        messagebox.showerror("Critical Error", str(e.args))

def check_finale(df):
    try:
        df.iloc[:,0] = pd.to_datetime(df.iloc[:,0],format='%H:%M:%S')
        first_sample = df.iloc[:,0].min()
        first_sample = pd.to_datetime(first_sample)
        first_minute_df = df[(df.iloc[:, 0] >= first_sample) & (df.iloc[:, 0] < first_sample + pd.Timedelta(minutes=1))]

        # Conta il numero di campioni nel primo minuto
        num_samples = len(first_minute_df)
        
        # Verifica se il numero di campioni è inferiore a 60
        if num_samples < 60:
            # Calcola il numero di valori 0 da aggiungere
            num_zeros = 60 - num_samples
            
            # Crea un DataFrame con i valori 0 da aggiungere
            zeros_df = pd.DataFrame({column: [0] * num_zeros for column in df.columns[0:]})
            zeros_df.iloc[:, 0] = first_sample
            # Concatena il DataFrame dei valori 0 al DataFrame originale
            df = pd.concat([zeros_df, df], ignore_index=True)
        return df
    except Exception as e:
        root=tk.Tk()
        root.withdraw()
        messagebox.showerror("Critical Error", str(e.args))


# Select user-chosen columns from dataframes
def select_2columns(df1, df2):
    try:
        global j
        global currentpage
        df1= remove_special_characters(df1)
        df2= remove_special_characters(df2)
        selection['File1'] = remove_special_characters_from_list(selection['File1'])
        selection['File2'] = remove_special_characters_from_list(selection['File2'])

        selected_df1 = df1[selection['File1']]  # Seleziona solo le colonne desiderate
        selected_df2 = df2[selection['File2']]  # Seleziona solo le colonne desiderate
        
        merged_df = pd.concat([selected_df1, selected_df2], axis=1)
        
        # Salva il DataFrame nel file CSV esistente con il secondo foglio
        with pd.ExcelWriter(output_file, mode='a', engine='openpyxl') as writer:
            merged_df.to_excel(writer, sheet_name='Data'+str(j), index=False)
        merged_df.to_csv('backup.csv', index=False)
        currentpage=j
        j=j+1
    except Exception as e:
        root=tk.Tk()
        root.withdraw()
        messagebox.showerror("Critical Error", str(e.args))

def select_columns(df1):
    try:
        global j
        global currentpage
        df1= remove_special_characters(df1)
   
        selection['File1'] = remove_special_characters_from_list(selection['File1'])
   
        try: 
            selected_df1 = df1[selection['File1']]  # Seleziona solo le colonne desiderate
        except KeyError:
            df1.columns = df1.iloc[0].tolist()
            df1.columns = df1.columns.astype(str)
          
            selected_df1 = df1[selection['File1']]  # Seleziona solo le colonne desiderate

        # Salva il DataFrame nel file CSV esistente con il secondo foglio
        with pd.ExcelWriter(output_file, mode='a', engine='openpyxl') as writer:
            selected_df1.to_excel(writer, sheet_name='Data'+str(j), index=False)
        selected_df1.to_csv('backup.csv', index=False)
        currentpage=j
        j=j+1
    except Exception as e:
        root=tk.Tk()
        root.withdraw()
        messagebox.showerror("Critical Error", str(e.args))

def upload_file(clickedfolder1, drop1, drop3,clickedcolumn1, file_list2, file_listbox, entry2):
    try:
        global clean_paths
        with open('options.txt') as f:
            lines = f.readlines() 
        temp=lines[0].rstrip('\n')
        for path in lines:
            
            clean = folder_path + '\\' + path.rstrip('\n')
            clean_paths.append(clean)

        with open('options_multi.txt', 'w') as f:
            for filename in clean_paths:
                f.write(filename + '\n')
        file_listbox.delete(0, tk.END)
        for file_name in lines:
            file_listbox.insert(tk.END, file_name)

        clickedfolder1.set(temp)
        load_file(drop1, drop3, temp, clickedcolumn1, file_list2, clickedfolder1, entry2, file_listbox)

    except Exception as e:
        root=tk.Tk()
        root.withdraw()
        messagebox.showerror("Critical Error", str(e.args))
    