import customtkinter as ctk
import tkinter as tk
import os
import sys
from src import guy  # Supponiamo che questo modulo crei la GUI principale

def remove_temp_files():
    files_to_remove = [
        'options_multi.txt', 'options.txt', 'options1.txt', 'options2.txt',
        'output0.csv', 'output1.csv', 'check.csv', 'data.csv', 'backup.csv',
        'backupdf2.csv', 'backupprova.csv', 'prova2.csv', 'plot.png',
        'prova.csv', 'prova1.csv', 'prova3.csv', 'output0_modified.csv',
        'output1_modified.csv', 'backupdf1.csv', 'backupdoasjfouieqhfiufho.csv',
        'output0check.csv', 'output1check.csv', 'options_event.txt',
        'interactive_plot.txt'
    ]
    for file in files_to_remove:
        if os.path.isfile(file):
            os.remove(file)

def show_main_window():
    # Impostazioni per la finestra principale
    ctk.set_appearance_mode('Dark')
    ctk.set_default_color_theme("dark-blue")
    
    root = ctk.CTk()  # Creiamo la finestra principale
    root.title("Test Data Analyzer 1.2V")
    
    # Dimensioni adattive per lo schermo
    main_width = 1200  
    main_height = 800
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - main_width) // 2
    y = (screen_height - main_height) // 2
    root.geometry(f"{main_width}x{main_height}+{x}+{y}")
    root.resizable(True, True)

    # Configurazione per espansione dinamica
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    
    # Creazione dell'interfaccia principale tramite il modulo guy
    guy.create_gui(root) 

    def on_closing():
        remove_temp_files()
        root.destroy()
        sys.exit()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

def main():
    # Creazione della splash screen con customtkinter per avere uno stile coerente
    splash = ctk.CTk()
    splash.title("Loading...")
    
    # Dimensioni contenute per la splash screen
    splash_width = 400
    splash_height = 150
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width - splash_width) // 2
    y = (screen_height - splash_height) // 2
    splash.geometry(f"{splash_width}x{splash_height}+{x}+{y}")
    splash.resizable(False, False)
    
    # Uso di grid() invece di pack()
    splash.grid_rowconfigure(0, weight=1)
    splash.grid_columnconfigure(0, weight=1)
    
    label = ctk.CTkLabel(splash, text="Loading Test Data Analyzer...", font=("Arial", 16))
    label.grid(row=0, column=0, pady=10, padx=10)
    
    progressbar = ctk.CTkProgressBar(splash, width=300)
    progressbar.grid(row=1, column=0, pady=10, padx=10)
    progressbar.set(0)
    
    progress = 0.0

    def update_progress():
        nonlocal progress
        progress += 0.01  # Incremento
        progressbar.set(progress)
        if progress < 1.0:
            splash.after(30, update_progress)
        else:
            splash.destroy()
            show_main_window()

    splash.after(0, update_progress)
    splash.mainloop()

if __name__ == "__main__":
    main()
