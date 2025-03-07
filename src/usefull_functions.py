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

def convert_to_relative_time(ms_col, reference_time):
    try:
    # Convert column to pandas Series
        ms_series = pd.Series(ms_col)

        # Get reference time as timedelta
        ref_td = pd.to_timedelta(reference_time)

        # Convert column to timedelta and add reference time
        relative_td = ref_td + pd.to_timedelta(ms_series, unit='ms')

        # Convert timedelta to string 
        relative_strings = relative_td.astype(str)

        return relative_strings
    except Exception as e:
        root=tk.Tk()

        root.withdraw()
        print(e)
        error_message = e.args
        messagebox.showerror("Critical Error", str(error_message))

def apply_formulas_to_column(df,reftime,column_date):
    # Validate input column is numeric
    try:
        
        time_column = df[column_date]

            # Make sure column is numeric before time conversion 
        df = df.copy()
        time_column = pd.to_numeric(time_column, errors='coerce')
    
        reftime_str = reftime.strftime('%H:%M:%S')
        reference_timedelta = pd.to_timedelta(reftime_str)
        
        if not isinstance(time_column[0], (int, float, str)):
            relative_times = convert_to_relative_time(df[column_date], reference_timedelta)
        
            df[column_date] = relative_times.apply(lambda x: str(x).split()[-1])

            return df
            #raise TypeError("Input column must be numeric or string")
        # Add reference time to column
        time_column = pd.to_timedelta(time_column, unit='s') + reference_timedelta

        # Round to seconds and convert to string
        time_column = time_column.dt.round('1s').apply(lambda x: str(x).split()[-1])
        # Replace column in copied DataFrame
        df[column_date] = time_column

        return df
    except Exception as e:
        root=tk.Tk()
        root.withdraw()
        print(e)
        error_message = e.args
        messagebox.showerror("Critical Error", str(error_message))

def align_dataframes(df1, df2, time_column1, time_column2):
    """
    Allinea solo l'inizio e la fine dei due DataFrame ad un tempo comune (global_start e global_end)
    aggiungendo delle righe di zero padding (a cadenza di 1 secondo) solo per coprire le parti mancanti.
    
    Ad esempio, se per df1:
      - start1 > global_start: viene creato un padding all'inizio (da global_start fino a start1 - 1 sec)
      - end1 < global_end:  viene creato un padding finale (da end1 + 1 sec fino a global_end)
    
    Lo stesso per df2.  
    I due DataFrame mantengono le loro colonne temporali indipendenti, e i nuovi timestamp
    sono formattati come hh:mm:ss.
    
    Parameters:
      df1, df2          : DataFrame da allineare
      time_column1      : nome della colonna temporale in df1
      time_column2      : nome della colonna temporale in df2
      
    Returns:
      tuple: (df1_allineato, df2_allineato)
    """
    # Creiamo copie dei DataFrame originali
    df1 = df1.copy()
    df2 = df2.copy()
    
    # Converte le colonne temporali in datetime
    df1[time_column1] = pd.to_datetime(df1[time_column1])
    df2[time_column2] = pd.to_datetime(df2[time_column2])
    
    # Calcola gli estremi (start ed end) per ciascun DataFrame
    start1 = df1[time_column1].min()
    end1   = df1[time_column1].max()
    start2 = df2[time_column2].min()
    end2   = df2[time_column2].max()
    
    # Determina il global start ed end (minimo dei due start, massimo dei due end)
    global_start = min(start1, start2)
    global_end   = max(end1, end2)
    delta_sec=(start1 - start2).total_seconds()

    # Identifica le colonne dei valori (cioè tutte quelle tranne la colonna temporale)
    value_columns1 = [col for col in df1.columns if col != time_column1]
    value_columns2 = [col for col in df2.columns if col != time_column2]
    
    # ----- Padding per df1 -----
    df1_list = []
    
    # Se il primo timestamp di df1 è successivo a global_start, crea il padding iniziale
    if start1 > global_start:
        pad_index = pd.date_range(start=global_start, end=start1 - pd.Timedelta(seconds=1), freq='s')
        pad_df1 = pd.DataFrame({time_column1: pad_index})
        for col in value_columns1:
            pad_df1[col] = 0
        df1_list.append(pad_df1)
    
    # Aggiungi il DataFrame originale
    df1_list.append(df1)
    
    # Se l'ultimo timestamp di df1 è precedente a global_end, crea il padding finale
    if end1 < global_end:
        pad_index = pd.date_range(start=end1 + pd.Timedelta(seconds=1), end=global_end, freq='s')
        pad_df1_end = pd.DataFrame({time_column1: pad_index})
        for col in value_columns1:
            pad_df1_end[col] = 0
        df1_list.append(pad_df1_end)
    
    # Concatena le parti e riordina in base alla colonna temporale
    df1_aligned = pd.concat(df1_list, ignore_index=True)
    df1_aligned = df1_aligned.sort_values(by=time_column1).reset_index(drop=True)
    
    # ----- Padding per df2 -----
    df2_list = []
    
    if start2 > global_start:
        pad_index = pd.date_range(start=global_start, end=start2 - pd.Timedelta(seconds=1), freq='s')
        pad_df2 = pd.DataFrame({time_column2: pad_index})
        for col in value_columns2:
            pad_df2[col] = 0
        df2_list.append(pad_df2)
    
    df2_list.append(df2)
    
    if end2 < global_end:
        pad_index = pd.date_range(start=end2 + pd.Timedelta(seconds=1), end=global_end, freq='s')
        pad_df2_end = pd.DataFrame({time_column2: pad_index})
        for col in value_columns2:
            pad_df2_end[col] = 0
        df2_list.append(pad_df2_end)
    
    df2_aligned = pd.concat(df2_list, ignore_index=True)
    df2_aligned = df2_aligned.sort_values(by=time_column2).reset_index(drop=True)
    
    # Formatto le colonne dei tempi in hh:mm:ss
    df1_aligned[time_column1] = df1_aligned[time_column1].dt.strftime('%H:%M:%S')
    df2_aligned[time_column2] = df2_aligned[time_column2].dt.strftime('%H:%M:%S')
    
    return df1_aligned, df2_aligned, delta_sec

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
