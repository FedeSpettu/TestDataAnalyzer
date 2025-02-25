import re
import pandas as pd
import csv
from datetime import datetime
import matplotlib
matplotlib.use('TkAgg')
from tkinter import messagebox
import sys
import tkinter as tk
from tkinter import filedialog
import os

def remove_special_characters(df):
    try:
        cols = list(df.columns)
        for i, col in enumerate(cols):
            if isinstance(col, str):
                cols[i] = col.encode('ascii', 'ignore').decode() 


        df.columns = cols
        return df
    except Exception as e:
        root=tk.Tk()
        root.withdraw()
        print(e)
        error_message = e.args
        messagebox.showerror("Critical Error", str(error_message))

def remove_special_characters_from_list(input_list):
    try:
        cleaned_list = [re.sub(r'[^\x00-\x7F]+', '', s) for s in input_list]
        return cleaned_list
    except Exception as e:
        root=tk.Tk()
        root.withdraw()
        print(e)
        error_message = e.args
        messagebox.showerror("Critical Error", str(error_message))

def is_date_column2(csv_file):
    try:
        df = pd.read_csv(csv_file, sep=',')
        colu=[]
        

        if 'Event' in df.columns:
            df = df.drop('Event', axis=1)
        df = df.dropna(how='any')
        df.to_csv('backupprova.csv', index=False)
        #df3=df3
        for col in df.columns:
            
            for i in range(len(df)):
                date_str = df.iloc[i, df.columns.get_loc(col)]
                
                date_str = str(date_str)
                date_str = date_str.replace("[", "").replace("]", "")
        
                for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M',
                            '%d/%m/%Y %H:%M', '%H:%M:%S'):
                    try:

                        datetime.strptime(date_str, fmt)
                        colu.append(col)
                        date_time = True
                        break
                           
                    except ValueError:
                        date_time = False
                        pass
                    except TypeError:
                        date_time = False
                        pass
                
                if date_time is True:
                    break
        if colu!=[]:
            return True, fmt, colu
        else:
            return False, None, None
    except Exception as e:
        root=tk.Tk()
        root.withdraw()
        print(e)
        error_message = e.args
        messagebox.showerror("Critical Error", str(error_message))

def convert_time_format(time_string):

  time_list = re.split(':', time_string)

  # Get the last element of the list of strings.
  last_element = time_list[-1]

  # Convert the last element of the list of strings to a float.
  float_value = float(last_element)

  return float_value

def is_date_column(csv_file):
    with open(csv_file) as f:
        reader = csv.reader(f)
        headers = next(reader)
        first_data_row = next(reader)
     
        date_col = None
        date_format = None
        for i, header in enumerate(headers):
           
            for row in reader:
                date_str = row[i]
               
                for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M',
                            '%d/%m/%Y %H:%M', '%H:%M:%S', '%H:%M:%S.%f', '%M:S%.%f','S%.%f', '%H:%M:%S:%f', '%H.%M.%S.%f','%H.%M.%S', '%d/%m/%Y@%H:%M:%S','%Y-%m-%d %H.%M.%S', '%M:%S.%f'):
                    try:
                        datetime.strptime(date_str, fmt)
                        date_col = header
                        date_format = fmt
                        break
                    except ValueError:
                        pass
                    
            if date_col is not None:
                
                pattern = '00:00:00'
                first_data_row = str(first_data_row[0])
           
                first_data_row = first_data_row.split('.')
             
                first_data_row = str(first_data_row[0])
                if pattern==first_data_row:
                
                    date_col=headers[0]
                    df = pd.read_csv(csv_file, sep=',', encoding='UTF-8', engine='python')
                    start_time = pd.to_datetime(first_data_row)
                    
                    df[date_col] = df[date_col].apply(lambda x: (pd.to_datetime(x) - start_time).total_seconds())
                    df.to_csv(csv_file, index=False)
                    return False, date_col, date_format
                else:
                    return True, date_col, date_format
        if date_col is None:
                date_col=headers[0]
        
    return False, date_col, date_format

# Check if string can be converted to float
def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False
    
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

# Check if string is formatted like datetime
def is_datetime(string):
    formats = ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M','%d/%m/%Y %H:%M', '%H:%M:%S', '%H:%M:%S.%f', '%Y-%m-%d', '%d-%m-%Y', '%H:%M:%S:%f', '%H.%M.%S.%f','%H.%M.%S', '%d/%m/%Y@%H:%M:%S','%Y-%m-%d %H.%M.%S']
    
    for format in formats:
        try:
            datetime.strptime(string, format)
            return True
            
        except ValueError:
            pass
    return False
    
        

# Try different delimiters on sample rows to guess CSV delimiter
def auto_detect_delimiter(file_path):
    try:
        _, file_extension = os.path.splitext(file_path)

        if file_extension.lower() == '.txt':
            return '\t'  # Return '\t' if the file has a .txt extension

        max_lines_to_check = 10  # Number of lines to analyze
        with open(file_path, 'r') as file:
            lines = [file.readline().strip() for _ in range(max_lines_to_check)]

        # Check for tabs first
        tab_counts = [line.count('\t') > 1 for line in lines]
        if all(tab_count for tab_count in tab_counts):
            return '\t'  # Return tab as delimiter

        # If tabs are not detected, check other delimiters
        potential_delimiters = [',', ';', '|', ' ']
        for delimiter in potential_delimiters:
            counts = [len(re.split(re.escape(delimiter), line)) > 1 for line in lines]

            if all(count for count in counts):
                return delimiter

        return '\s\s+'
    except Exception as e:
        root=tk.Tk()
        root.withdraw()
        print(e)
        error_message = e.args
        messagebox.showerror("Critical Error", str(error_message))
