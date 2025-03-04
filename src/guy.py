from src import dataload as dl, statanalysis as st  # e selectfoldergui se necessario
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from src.global_var import *
from PIL import Image, ImageTk, ImageSequence
from src.usefull_functions import auto_detect_delimiter
import time



# --- Utility Functions --- #
def folderanalysis(clean_paths, drop1, drop2, clickedfolder1, clickedfolder2, file_list2,
                     text_input1, text_input2, text_input3, checkbox_var, checkbox_var1,
                     var_unit, checkbox_var2, text_input4, text_input5, var_unit3, var_unit2,
                     drop3, file_list3, frame1, frame2, frame3, input_frame,
                     checkbox_var3, clickedeventstart, clickedeventend, enable_plot):
    """
    Funzione che richiama la procedura di analisi su più file (il contenuto è gestito da statanalysis).
    """
    global selection
    i = 0
    clean_path = []
    if os.path.isfile('options_multi.txt'):
        with open('options_multi.txt') as f:
            lines = f.readlines()
        for path in lines:
            clean = path.rstrip('\n')
            clean_path.append(clean)
    n_files = len(clean_path)
    st.loading_fun_mult(text_input1.get(), text_input2.get(), text_input3.get(),checkbox_var.get(), checkbox_var1.get(),var_unit,checkbox_var2.get(), text_input4, text_input5,clickedfolder2,clickedfolder1, var_unit3, var_unit2, i, n_files, clean_path,drop1, drop3, file_list3, frame1, frame2, frame3, input_frame, checkbox_var3, clickedeventstart,clickedeventend, enable_plot)


def destroy(root):
    root.destroy()
    exit()

def second_folder(frame3, switch):
    if switch:
        frame3.grid()  # mostra
    else:
        frame3.grid_remove()

def add_title_to_frame(frame, title):
    title_label = tk.Label(frame, text=title, background='#FFD700', font=('Helvetica', 10, 'bold'))
    title_label.place(relx=0, rely=0, anchor='nw')

# Global dictionary to gestire lo stato dei pulsanti
buttons = {}

def checkbox_checked(checkbox_var3, drop_start, drop_end, file_list6, file_list5,
                     entry5, entry6, clickedeventstart, clickedeventend, *args):
    # Filtra gli eventi basandosi sui termini di ricerca
    search_term5 = entry5.get().lower()
    search_term6 = entry6.get().lower()
    if checkbox_var3.get():
        delimiter = auto_detect_delimiter('output0.csv')
        df = pd.read_csv('output0.csv', sep=delimiter, encoding='UTF-8')
        df = df.dropna(subset=['Event'])
        df['Event'] = df['Event'].astype(str)
        df['Event_lower'] = df['Event'].str.lower()
        df_filtered5 = df[df['Event_lower'].str.contains(search_term5)]
        df_filtered6 = df[df['Event_lower'].str.contains(search_term6)]
        ITEMS_PER_PAGE = 20
        def truncate_event(event_string, max_chars=100):
            return event_string[:max_chars] + "..." if len(event_string) > max_chars else event_string
        def on_select_start(full_event):
            updatetxt(full_event, file_list5, df['Event'], drop_start)
        def on_select_end(full_event):
            updatetxt(full_event, file_list6, df['Event'], drop_end)
        def update_drop_start_menu(page=0, repost=False):
            menu = drop_start["menu"]
            menu.delete(0, "end")
            start = page * ITEMS_PER_PAGE
            end = start + ITEMS_PER_PAGE
            current_slice = df_filtered5.iloc[start:end]
            for row in current_slice.itertuples():
                idx = row.Index
                full_event = str(idx)+ '@#@'+ row.Event
                truncated_event = truncate_event(full_event, max_chars=20)
                display_text = f'{full_event}'
                menu.add_command(label=display_text, command=lambda value=full_event: on_select_start(value))
            if end < len(df_filtered5):
                menu.add_command(label="More >>", command=lambda: update_drop_start_menu(page + 1, repost=True))
            if page > 0:
                menu.add_command(label="<< Previous", command=lambda: update_drop_start_menu(page - 1, repost=True))
            if repost:
                x = drop_start.winfo_rootx()
                y = drop_start.winfo_rooty() + drop_start.winfo_height()
                menu.post(x, y)
        def update_drop_end_menu(page=0, repost=False):
            menu = drop_end["menu"]
            menu.delete(0, "end")
            start = page * ITEMS_PER_PAGE
            end = start + ITEMS_PER_PAGE
            current_slice = df_filtered6.iloc[start:end]
            for row in current_slice.itertuples():
                idx = row.Index
                full_event = str(idx)+ '@#@'+ row.Event
                truncated_event = truncate_event(full_event, max_chars=20)
                display_text = f'{full_event}'
                menu.add_command(label=display_text, command=lambda value=full_event: on_select_end(value))
            if end < len(df_filtered6):
                menu.add_command(label="More >>", command=lambda: update_drop_end_menu(page + 1, repost=True))
            if page > 0:
                menu.add_command(label="<< Previous", command=lambda: update_drop_end_menu(page - 1, repost=True))
            if repost:
                x = drop_end.winfo_rootx()
                y = drop_end.winfo_rooty() + drop_end.winfo_height()
                menu.post(x, y)
        update_drop_start_menu(page=0)
        update_drop_end_menu(page=0)

selection_event = []

def updatetxt(value, file_list, event_to_index, drop):
    file_list.insert(tk.END, value)
    selection_event.append(value)
    with open('options_event.txt', 'w') as f:
         for filename in selection_event:
             f.write(filename + '\n')

def multi_select(var_multiple):
    global buttons
    if var_multiple:
        buttons["analyze_file_button"].configure(state='enable', fg_color='orange', text_color='black')
        buttons["folder_button2"].configure(state='enable', fg_color='orange', text_color='black')
        buttons["upload_button"].configure(state='enable', fg_color='orange', text_color='black')
        buttons["analyze_button"].configure(state='disabled')
        buttons["switch"].configure(state='disabled')
        buttons['drop1'].configure(state='disabled')
    else:
        buttons["analyze_file_button"].configure(state='disabled', fg_color='gray', text_color='black')
        buttons["folder_button2"].configure(state='disabled', fg_color='gray', text_color='black')
        buttons["upload_button"].configure(state='disabled', fg_color='gray', text_color='black')
        buttons["analyze_button"].configure(state='enable')
        buttons["switch"].configure(state='enable')
        buttons['drop1'].config(state='normal', bg="#1f538d", fg='white',
                                activebackground="#14375e", activeforeground='white', width=15)

def clear_placeholder(entry_widget):
    entry_widget.grid_forget()

def remove_event(file_list, file_txt, drop):
    global selection_event
    selected_index = file_list.curselection()
    drop.config(state='normal', bg="#1f538d", fg='white',
                activebackground="#14375e", activeforeground='white', width=15)
    if selected_index:
        selected_item = file_list.get(selected_index)
        file_list.delete(selected_index)
        selection_event.remove(selected_item)
        with open(file_txt, "r") as file:
            lines = file.readlines()
        updated_lines = [line for line in lines if line.strip() != selected_item.strip()]
        with open(file_txt, "w") as file:
            file.writelines(updated_lines)

def remove_selected(file_list, file_txt, file_key):
    global selection
    # Get the index and value of the currently selected item.
    selected_index = file_list.curselection()
    if selected_index:
        selected_item = file_list.get(selected_index)
        file_list.delete(selected_index)
        # Remove the item from the correct list in the selection dictionary.
        if file_key in selection and selected_item in selection[file_key]:
            selection[file_key].remove(selected_item)
        # Read all lines from the file.
        with open(file_txt, "r") as file:
            lines = file.readlines()
        # Rewrite the file, omitting the line that exactly matches the selected item.
        with open(file_txt, "w") as file:
            for line in lines:
                if line.strip() != selected_item:
                    file.write(line)



# Global dictionary to hold button references if needed
buttons = {}

def create_gui(root):
    
    # Configure the root window
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # Create a Canvas for Scrolling
    canvas = tk.Canvas(root, bg="#2E2E2E", highlightthickness=0)
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    
    main_frame = ctk.CTkFrame(root, fg_color="#2E2E2E")
    main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    main_frame.grid_rowconfigure(0, weight=0)   # OUTPUT section
    main_frame.grid_rowconfigure(1, weight=1)   # INPUT section
    main_frame.grid_rowconfigure(2, weight=2)   # ANALYSIS section
    main_frame.grid_columnconfigure(0, weight=1)
    # Configure Scroll Region
    main_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # Frame Window in Canvas
    frame_window = canvas.create_window((0, 0), window=main_frame, anchor="nw")

    # Scroll Configurations
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Place Widgets
    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")

    # Set the scrollable frame to expand
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # Fill the scrollable frame with your UI elements
    populate_scrollable_frame(main_frame)

def populate_scrollable_frame(main_frame):
    # Common values for option menus
    units = ['N/A', 'Pa', 'bar', 'mmHg', 'Torr', 'mm', 'cm', 'm', 'km',
             'in', 'ft', 'yd', 'mi', 'm2', 'km2', 'ha', 'ac', 'L', 'mL',
             'g', 'kg', 's', 'min', 'h', '°C', '°F', 'rad', '°', 'Hz', 'V', 'A', 'W']
    conditions = ['x<Limit1', 'x>Limit1', 'Limit1<x<Limit2', 'x<Limit1 or x>Limit2',
                  'x<=Limit1', 'x>=Limit1', 'Limit1<=x<=Limit2', 'x=Limit1']
    files=[]
    first_row = []
    global buttons
    global clean_paths
    output_file = None
    output_path = None
    startup=True
    # -------------------------------
    # OUTPUT SECTION (Step 1)
    # -------------------------------
    output_frame = ctk.CTkFrame(main_frame, fg_color="#3B3B3B", corner_radius=10,
                                border_width=2, border_color="#FFD700")
    output_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
    output_frame.grid_columnconfigure(2, weight=2)
    output_label = ctk.CTkLabel(output_frame, text="Step 1: Output Selection",
                                font=ctk.CTkFont(size=16, weight="bold"))
    output_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
    clear_all_button = ctk.CTkButton(output_frame, text="Clear All",
                                     fg_color="#CC3333", text_color="white",
                                     font=ctk.CTkFont(size=12, weight="bold"),
                                     width=80,
                                     command=lambda: call_reset(elements))
    clear_all_button.grid(row=1, column=2, padx=10, pady=5, sticky="e")
    output_folder_button = ctk.CTkButton(output_frame, text="Select Output Folder",
                                         command=lambda: st.select_output(output_folder_label, clean_paths,
        output_folder_label,
        file1_optionmenu,
        file1_optionmenu_var,
        file2_optionmenu_var,
        file1_listboxfile,
        limit1_entry,
        limit2_entry, 
        nvalues_entry,
        checkbox_threshold,
        checkbox_align,
        unit_var,
        checkbox_plot,
        condition_var,
        pass_fail_var,
        file1_column_option,
        file1_listbox,
        output_frame,
        file1_frame,
        file2_frame,
        analysis_frame,
        checkbox_event,
        start_event_var,
        end_event_var,
        file1_folder_label,
        file2_folder_label,
        start_event_option,
        end_event_option,
        event_listbox2,
        event_listbox1,
        event_filter_entry1,
        event_filter_entry2,
        unit_option_menu,
        file2_column_option_var,
        file1_column_option_var,
        checkbox_advance))
    output_folder_button.grid(row=1, column=0, padx=10, pady=5, sticky="w")
    output_folder_label = ctk.CTkLabel(output_frame, text="No folder selected", width=100)
    output_folder_label.grid(row=1, column=1, padx=10, pady=5, sticky="w")

    # -------------------------------
    # INPUT SECTION
    # -------------------------------
    input_frame = ctk.CTkFrame(main_frame, fg_color="#3E3E3E", corner_radius=10,
                               border_width=2, border_color="#FFD700")
    input_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
    input_frame.grid_columnconfigure(0, weight=1)
    input_frame.grid_columnconfigure(1, weight=1)
    input_title = ctk.CTkLabel(input_frame, text="Step 2: Input Selection",
                               font=ctk.CTkFont(size=16, weight="bold"))
    input_title.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")

    # ---- File 1 Selection Area with Multi File Selection ----
    file1_frame = ctk.CTkFrame(input_frame, fg_color="#4A4A4A", corner_radius=10,
                               border_width=1, border_color="#FFD700")
    file1_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
    file1_frame.grid_rowconfigure(4, weight=1)
    file1_title = ctk.CTkLabel(file1_frame, text="File 1 Selection",
                               font=ctk.CTkFont(size=14, weight="bold"))
    file1_title.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")
    # Row 1: Browse Folder
    file1_browse_button = ctk.CTkButton(file1_frame, text="Browse Folder 1",
                                        width=140,
                                        command=lambda: dl.select_folder(
                                          file1_listboxfile,
                                          file1_optionmenu,
                                          file1_column_option,
                                          file1_optionmenu_var,
                                          file1_column_option_var,
                                          file1_folder_label,
                                          file1_listbox,
                                          file1_file_filter_entry,
                                          file1_column_filter_entry))
    file1_browse_button.grid(row=1, column=0, padx=10, pady=5, sticky="w")
    file1_folder_label = ctk.CTkLabel(file1_frame, text="No folder selected", width=100)
    file1_folder_label.grid(row=1, column=1,columnspan=2, padx=10, pady=5, sticky="w")
    # Row 2: Multi File Controls (unchanged)
    multi_file_inner_frame = ctk.CTkFrame(file1_frame, fg_color="#3E3E3E", corner_radius=10,
                                          border_width=2, border_color="#FFD700")
    multi_file_inner_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=10, pady=5)
    multi_file_switch = ctk.CTkSwitch(multi_file_inner_frame, text="Multi Select", command=lambda: multi_select(multi_file_switch.get()))
    multi_file_switch.grid(row=0, column=0, padx=10, pady=5)
    pick_files_button = ctk.CTkButton(multi_file_inner_frame, text="Pick Files",
                                      command=dl.create_g)
    pick_files_button.grid(row=0, column=1, padx=10, pady=5)
    upload_files_button = ctk.CTkButton(multi_file_inner_frame, text="Upload Files",
                                        command=lambda: dl.upload_file(
                                          file1_optionmenu_var,
                                          file1_optionmenu,
                                          file1_column_option,
                                          file1_column_option_var,
                                          file1_listbox,
                                          file1_listboxfile,
                                          file1_file_filter_entry
                                      ))
    upload_files_button.grid(row=0, column=2, padx=10, pady=5)
    
    # Row 3: OptionMenus with Filters for File 1
    # -- File selection with filter --
    file1_file_frame = ctk.CTkFrame(file1_frame)
    file1_file_frame.grid(row=3, column=0, padx=10, pady=5, sticky="w")
    file1_file_filter_entry = ctk.CTkEntry(file1_file_frame, placeholder_text="Filter file")
    file1_file_filter_entry.grid(row=0, column=0, padx=2, pady=2)
    # When the user presses Return, update the file option menu based on the filter text.
    file1_file_filter_entry.bind("<KeyRelease>", lambda event: dl.update_option_menu(
        files,  # Need to maintain list of files
        file1_optionmenu, 
        file1_column_option,
        file1_optionmenu_var,
        file1_column_option_var,
        file1_listbox,
        file1_file_filter_entry,
        file1_column_filter_entry,
        file1_listboxfile
    ))
    file1_optionmenu_var = tk.StringVar(file1_file_frame)
    file1_optionmenu_var.set("Select File")
    file1_optionmenu = tk.OptionMenu(file1_file_frame,file1_optionmenu_var, value=["Select File"])
    file1_optionmenu.config(bg="#20548b", fg='white', width=15)
    file1_optionmenu.grid(row=1, column=0, padx=10, pady=5)
    
    # -- Column selection with filter --
    file1_column_frame = ctk.CTkFrame(file1_frame)
    file1_column_frame.grid(row=3, column=1, padx=10, pady=5, sticky="w")
    file1_column_filter_entry = ctk.CTkEntry(file1_column_frame, placeholder_text="Filter column")
    file1_column_filter_entry.grid(row=0, column=0, padx=2, pady=2)
    file1_column_filter_entry.bind("<KeyRelease>", lambda event: dl.update_option_column(
        first_row,  # Need to maintain first row data
        file1_column_option,
        file1_column_option_var,
        file1_listbox,
        file1_column_filter_entry,
        k=0
    ))
    file1_column_option_var = tk.StringVar(file1_column_frame)
    file1_column_option_var.set("Select Column")
    file1_column_option = tk.OptionMenu(file1_column_frame,file1_column_option_var, value=["Select column"])
    file1_column_option.config(bg="#20548b", fg='white', width=15)
    file1_column_option.grid(row=1, column=0, padx=10, pady=5)
    
    # -- Unit OptionMenu (no filter needed) --
    unit_var = tk.StringVar(file1_frame)
    unit_var.set(units[0])
    unit_option_menu = ctk.CTkOptionMenu(file1_frame, variable=unit_var, values=units)
    #unit_option_menu.config(bg="#20548b", fg='white', width=15)
    unit_option_menu.grid(row=3, column=2, padx=10, pady=5, sticky="w")
    
    # Row 4: Listbox (unchanged)
    file1_listboxfile = tk.Listbox(file1_frame, height=4, width=30)
    file1_listboxfile.grid(row=4, column=0, columnspan=1, padx=10, pady=5, sticky="ew")
    
    file1_listbox = tk.Listbox(file1_frame, height=4, width=30)
    file1_listbox.grid(row=4, column=1, columnspan=1, padx=10, pady=5, sticky="ew")
    file1_listbox.bind("<Button-1>", lambda event: remove_selected(file1_listbox, 'options1.txt', 'File1'))

    # ---- File 2 Selection Area (Optional) ----
    file2_frame = ctk.CTkFrame(input_frame, fg_color="#4E4E4E", corner_radius=10,
                               border_width=1, border_color="#FFD700")
    file2_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)
    file2_header = ctk.CTkFrame(file2_frame, fg_color="#4E4E4E", corner_radius=5)
    file2_header.grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
    file2_header.grid_columnconfigure(0, weight=1)
    file2_title = ctk.CTkLabel(file2_header, text="File 2 Selection (Optional)",
                               font=ctk.CTkFont(size=14, weight="bold"))
    file2_title.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")
    # Row 1: Browse Folder and Enable Switch
    file2_browse_button = ctk.CTkButton(file2_frame, text="Browse Folder 2",
                                        width=140,state="disabled",
                                        command=lambda: dl.select_folder(
                                          file2_listboxfile,
                                          file2_optionmenu,
                                          file2_column_option,
                                          file2_optionmenu_var,
                                          file2_column_option_var,
                                          file2_folder_label,
                                          file2_listbox,
                                          file2_file_filter_entry,
                                          file2_column_filter_entry
                                      ))
    file2_browse_button.grid(row=1, column=0, padx=10, pady=5, sticky="w")
    
    file2_folder_label = ctk.CTkLabel(file2_frame, text="No folder selected", width=100)
    file2_folder_label.grid(row=1, column=1,columnspan=1, padx=10, pady=5, sticky="w")
    file2_switch_var = tk.BooleanVar(value=False)
    file2_enable_switch = ctk.CTkSwitch(file2_frame, text="Enable File 2",
                                        command=lambda: toggle_file2_buttons(),
                                        variable=file2_switch_var)
    file2_enable_switch.grid(row=1, column=2, padx=10, pady=5, sticky="w")

    file2_frame.grid_rowconfigure(2, minsize=45)
    
    # Row 3: OptionMenus with Filters for File 2
    # -- File selection with filter --
    file2_file_frame = ctk.CTkFrame(file2_frame)
    file2_file_frame.grid(row=3, column=0, padx=10, pady=5, sticky="w")
    file2_file_filter_entry = ctk.CTkEntry(file2_file_frame, placeholder_text="Filter file")
    file2_file_filter_entry.grid(row=0, column=0, padx=2, pady=2)
    file2_file_filter_entry.bind("<KeyRelease>", lambda event: dl.update_option_menu(
        files,  # Need to maintain list of files
        file2_optionmenu, 
        file2_column_option,
        file2_optionmenu_var,
        file2_column_option_var,
        file2_listbox,
        file2_file_filter_entry,
        file2_column_filter_entry,
        file2_listboxfile
    ))
    file2_optionmenu_var = tk.StringVar(file2_file_frame)
    file2_optionmenu_var.set("Select File")
    file2_optionmenu = tk.OptionMenu(file2_file_frame,file2_optionmenu_var, value=["Select file"])
    file2_optionmenu.config(bg="#20548b", fg='white', width=15)
    file2_optionmenu.grid(row=1, column=0, padx=10, pady=5)
    
    # -- Column selection with filter --
    file2_column_frame = ctk.CTkFrame(file2_frame)
    file2_column_frame.grid(row=3, column=1, padx=10, pady=5, sticky="w")
    file2_column_filter_entry = ctk.CTkEntry(file2_column_frame, placeholder_text="Filter column")
    file2_column_filter_entry.grid(row=0, column=0, padx=2, pady=2)
    file2_column_filter_entry.bind("<KeyRelease>", lambda event: dl.update_option_column(
        first_row,
        file2_column_option,
        file2_column_option_var,
        file2_listbox,
        file2_column_filter_entry,
        k=1
    ))
    file2_column_option_var = tk.StringVar(file2_column_frame)
    file2_column_option_var.set("Select Column")
    file2_column_option = tk.OptionMenu(file2_column_frame,file2_column_option_var, value=["Select column"])
    file2_column_option.config(bg="#20548b", fg='white', width=15)
    file2_column_option.grid(row=1, column=0, padx=10, pady=5)
    
    # Row 4: Listbox (unchanged)
    file2_listboxfile = tk.Listbox(file2_frame, height=4, width=30)
    file2_listboxfile.grid(row=4, column=0, columnspan=1, padx=10, pady=5, sticky="ew")
    
    file2_listbox = tk.Listbox(file2_frame, height=4, width=30)
    file2_listbox.grid(row=4, column=1, columnspan=1, padx=10, pady=5, sticky="ew")
    file2_listbox.bind("<Button-1>", lambda event: remove_selected(file2_listbox, 'options2.txt', 'File2'))
    def toggle_file2_buttons():
    
        state = "normal" if file2_enable_switch.get() else "disabled"
                
        file2_browse_button.configure(state=state)
        file2_folder_label.configure(state=state)
        file2_optionmenu.configure(state=state)
        file2_column_option.configure(state=state)
        file2_file_filter_entry.configure(state=state)
        file2_column_filter_entry.configure(state=state)
        file2_listboxfile.configure(state=state)
        file2_listbox.configure(state=state)    
        

    if startup:
        toggle_file2_buttons()
        startup = False
    # -------------------------------
    # ANALYSIS SECTION
    # -------------------------------
    analysis_frame = ctk.CTkFrame(main_frame, fg_color="#3B3B3E", corner_radius=10,
                                  border_width=2, border_color="#FFD700")
    analysis_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
    analysis_frame.grid_columnconfigure(0, weight=1)
    analysis_frame.grid_columnconfigure(1, weight=1)
    analysis_frame.grid_columnconfigure(2, weight=1)
    analysis_title = ctk.CTkLabel(analysis_frame, text="Step 3: Analysis",
                                  font=ctk.CTkFont(size=16, weight="bold"))
    analysis_title.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky="w")
    # (The remainder of your analysis section remains as before)
    options_buttons_frame = ctk.CTkFrame(analysis_frame, fg_color="#4A4A4A",
                                         corner_radius=5, border_width=1, border_color="#FFD700")
    options_buttons_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
    options_buttons_frame.grid_columnconfigure(0, weight=1)
    options_buttons_frame.grid_columnconfigure(1, weight=0)
    
    checkbox_align = ctk.BooleanVar(options_buttons_frame)
    checkbox_plot = ctk.BooleanVar(options_buttons_frame)
    checkbox_threshold = ctk.BooleanVar(options_buttons_frame)
    checkbox_event = ctk.BooleanVar(options_buttons_frame)
    options_frame_inner = ctk.CTkFrame(options_buttons_frame, fg_color="#4A4A4A", corner_radius=0)
    options_frame_inner.grid(row=0, column=0, sticky="w", padx=5, pady=5)
    threshold_cb = ctk.CTkCheckBox(options_frame_inner, text="Threshold", variable=checkbox_threshold)
    threshold_cb.grid(row=0, column=0, padx=5, pady=5)
    alignment_cb = ctk.CTkCheckBox(options_frame_inner, text="Alignment", variable=checkbox_align)
    alignment_cb.grid(row=0, column=1, padx=5, pady=5)
    plot_cb = ctk.CTkCheckBox(options_frame_inner, text="Plot", variable=checkbox_plot)
    plot_cb.grid(row=0, column=3, padx=5, pady=5)
    event_cb = ctk.CTkCheckBox(options_frame_inner, text="Event", variable=checkbox_event)
    event_cb.grid(row=0, column=2, padx=5, pady=5)
    
    checkbox_advance = ctk.BooleanVar(value=enable_plot)
    # Create the checkbox and assign the callback function with the command parameter
    def update_enable_plot():
        global enable_plot
        # Set enable_plot based on the checkbox state
        enable_plot = checkbox_advance.get()
        print("enable_plot is now:", enable_plot)

    advance_plot = ctk.CTkCheckBox(
        options_frame_inner,
        text="Interactive Plot",
        variable=checkbox_advance,
        command=update_enable_plot  # This is called when the checkbox is toggled
    )
    advance_plot.grid(row=0, column=4, padx=5, pady=5)
    
    # -------------------------------
    buttons_frame = ctk.CTkFrame(options_buttons_frame, fg_color="#4A4A4A", corner_radius=0)
    buttons_frame.grid(row=0, column=1, sticky="e", padx=5, pady=5)
    analyze_file_button = ctk.CTkButton(buttons_frame, text="Analyze File",
        command=lambda: st.loading_fun(
            limit1_entry.get(),
            limit2_entry.get(), 
            nvalues_entry.get(),
            checkbox_threshold.get(), #checkbox
            checkbox_align.get(), #checkbox1
            unit_var,
            checkbox_plot.get(), #checkbox2
            start_time1_entry,
            start_time2_entry,
            file2_optionmenu_var,
            file1_optionmenu_var,
            condition_var,
            pass_fail_var,
            1,  # i
            1,  # n_files
            output_frame,
            file1_frame,
            file2_frame,
            analysis_frame,
            checkbox_event.get(),
            start_event_var,
            end_event_var,
            enable_plot
        ))
    analyze_file_button.grid(row=0, column=0, padx=5, pady=5)
    analyze_folder_button = ctk.CTkButton(buttons_frame, text="Start Folder Analysis",
        fg_color='gray', text_color='black',
        command=lambda: folderanalysis(
            clean_paths,
            file1_optionmenu,
            file1_optionmenu,
            file1_optionmenu_var,
            file2_optionmenu_var,
            file1_listboxfile,
            limit1_entry,
            limit2_entry, 
            nvalues_entry,
            checkbox_threshold,
            checkbox_align,
            unit_var,
            checkbox_plot,
            start_time1_entry,
            start_time2_entry,
            condition_var,
            pass_fail_var,
            file1_column_option,
            file1_listbox,
            output_frame,
            file1_frame,
            file2_frame,
            analysis_frame,
            checkbox_event.get(),
            start_event_var,
            end_event_var, 
            enable_plot
        ))
    analyze_folder_button.grid(row=0, column=1, padx=5, pady=5)

    # Threshold Settings
    threshold_frame = ctk.CTkFrame(analysis_frame, fg_color="#4A4A4A",
                                   corner_radius=5, border_width=1, border_color="#FFD700")
    threshold_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
    threshold_title = ctk.CTkLabel(threshold_frame, text="Threshold Settings",
                                   font=ctk.CTkFont(size=14, weight="bold"))
    threshold_title.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")
    limit1_label = ctk.CTkLabel(threshold_frame, text="Limit1")
    limit1_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
    limit1_entry = ctk.CTkEntry(threshold_frame, width=100)
    limit1_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
    limit2_label = ctk.CTkLabel(threshold_frame, text="Limit2")
    limit2_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
    limit2_entry = ctk.CTkEntry(threshold_frame, width=100)
    limit2_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
    nvalues_label = ctk.CTkLabel(threshold_frame, text="N values")
    nvalues_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
    nvalues_entry = ctk.CTkEntry(threshold_frame, width=100)
    nvalues_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")
    condition_var = tk.StringVar(threshold_frame)
    condition_var.set(conditions[1])
    condition_option_menu = ctk.CTkOptionMenu(threshold_frame, variable=condition_var, values=conditions)
    #condition_option_menu.config(bg="#20548b", fg='white', width=15)
    condition_option_menu.grid(row=4, column=0, padx=10, pady=5, sticky="w")
    pass_fail_var = tk.StringVar(threshold_frame)
    options=['Pass', 'Fail']
    pass_fail_var.set(options[1])
    pass_failmenu = ctk.CTkOptionMenu(threshold_frame, variable=pass_fail_var, values=options)
    pass_failmenu.grid(row=4, column=1, padx=10, pady=5, sticky="w")
    # Alignment Settings
    alignment_frame = ctk.CTkFrame(analysis_frame, fg_color="#4A4A4A",
                                   corner_radius=5, border_width=1, border_color="#FFD700")
    alignment_frame.grid(row=2, column=1, padx=10, pady=5, sticky="nsew")
    alignment_title = ctk.CTkLabel(alignment_frame, text="Alignment Settings",
                                   font=ctk.CTkFont(size=14, weight="bold"))
    alignment_title.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")
    st1_label = ctk.CTkLabel(alignment_frame, text="Start Time 1")
    st1_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
    stringtime1 = ctk.StringVar(alignment_frame, value="00:00:00")
    stringtime2 = ctk.StringVar(alignment_frame,value="00:00:00")
    start_time1_entry = ctk.CTkEntry(alignment_frame, width=100, textvariable=stringtime1)
    start_time1_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
    st2_label = ctk.CTkLabel(alignment_frame, text="Start Time 2")
    st2_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
    start_time2_entry = ctk.CTkEntry(alignment_frame, width=100, textvariable=stringtime2)
    start_time2_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

    # Event Settings
    event_frame = ctk.CTkFrame(analysis_frame, fg_color="#4A4A4A",
                               corner_radius=5, border_width=1, border_color="#FFD700")
    event_frame.grid(row=2, column=2, padx=10, pady=5, sticky="nsew")
    event_title = ctk.CTkLabel(event_frame, text="Event Settings",
                               font=ctk.CTkFont(size=14, weight="bold"))
    event_title.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")
    start_event_var = tk.StringVar(event_frame)
    start_event_var.set("Start event")
    end_event_var = tk.StringVar(event_frame)
    end_event_var.set("End event")
    event_box1 = ctk.CTkFrame(event_frame)
    event_box1.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
    start_event_option = tk.OptionMenu(event_box1, variable=start_event_var, value=["Start event"])
    start_event_option.config(bg="#20548b", fg='white', width=15)
    start_event_option.grid(row=0, column=0, padx=2, pady=2)
    event_filter_entry1 = ctk.CTkEntry(event_box1, width=100, placeholder_text="Filter event")
    event_filter_entry1.grid(row=0, column=1, padx=2, pady=2)
    checkbox_event.trace("w", lambda *args: checkbox_checked(
        checkbox_event,
        start_event_option,
        end_event_option,
        event_listbox2,
        event_listbox1,
        event_filter_entry1,
        event_filter_entry2,
        start_event_var,
        end_event_var
    ))
    event_filter_entry1.bind("<Return>", lambda event: checkbox_checked(
        checkbox_event,
        start_event_option,
        end_event_option,
        event_listbox2,
        event_listbox1,
        event_filter_entry1,
        event_filter_entry2,
        start_event_var,
        end_event_var
    ))
    event_box2 = ctk.CTkFrame(event_frame)
    event_box2.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
    end_event_option = tk.OptionMenu(event_box2, variable=end_event_var, value=["End event"])
    end_event_option.config(bg="#20548b", fg='white', width=15)
    end_event_option.grid(row=0, column=0, padx=2, pady=2)
    event_filter_entry2 = ctk.CTkEntry(event_box2, width=100, placeholder_text="Filter event")
    event_filter_entry2.grid(row=0, column=1, padx=2, pady=2)
    event_filter_entry2.bind("<Return>", lambda event: checkbox_checked(
        checkbox_event,
        start_event_option,
        end_event_option,
        event_listbox2,
        event_listbox1,
        event_filter_entry1,
        event_filter_entry2,
        start_event_var,
        end_event_var
    ))
    event_listbox1 = tk.Listbox(event_frame, height=2, width=30)
    event_listbox1.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
    event_listbox1.bind("<Button-1>", lambda event: remove_event(event_listbox1, 'options_event.txt', start_event_option))
    event_listbox2 = tk.Listbox(event_frame, height=2, width=30)
    event_listbox2.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
    event_listbox2.bind("<Button-1>", lambda event: remove_event(event_listbox2, 'options_event.txt', end_event_option))
    # -------------------------------
    # MULTI-SELECT STATE MANAGEMENT
    # -------------------------------
    def set_state_frame(frame, state):
        """Recursively set the state of all widgets (if they support it) within a frame."""
        for child in frame.winfo_children():
            try:
                child.configure(state=state)
            except Exception:
                pass

    def multi_select_callback():
        """Enable or disable widgets based on the multi-select switch."""
        if multi_file_switch.get():
            pick_files_button.configure(state="normal")
            upload_files_button.configure(state="normal")
            analyze_folder_button.configure(state="normal")
            file1_optionmenu.configure(state="disabled")
            analyze_file_button.configure(state="disabled")
            set_state_frame(file2_frame, "disabled")
        else:
            pick_files_button.configure(state="disabled")
            upload_files_button.configure(state="disabled")
            analyze_folder_button.configure(state="disabled")
            file1_optionmenu.configure(state="normal")
            analyze_file_button.configure(state="normal")
            set_state_frame(file2_frame, "normal")

    # Initialize multi-select state
    pick_files_button.configure(state="disabled")
    upload_files_button.configure(state="disabled")
    analyze_folder_button.configure(state="disabled")
    multi_file_switch.configure(command=multi_select_callback)
    multi_select_callback()  # initial call

    # -------------------------------
    # SAVE REFERENCES (if needed for state management)
    # -------------------------------
    global buttons
    buttons = {
        "analyze_folder_button": analyze_folder_button,
        "analyze_file_button": analyze_file_button,
        "file1_optionmenu": file1_optionmenu,
        "folder_button2": pick_files_button,
        "upload_button": upload_files_button,
        "start_event_option": start_event_option,
        "end_event_option": end_event_option,
        "switch": file2_enable_switch,
        "drop1": file1_optionmenu,
        "drop5": start_event_option,
        "drop6": end_event_option
    }

    # -------------------------------
    # Clear GUI elements
    # -------------------------------
    elements = [
        clean_paths,
        output_folder_label,
        file1_optionmenu,
        file1_optionmenu_var,
        file2_optionmenu_var,
        file1_listboxfile,
        file2_listboxfile,
        limit1_entry,
        limit2_entry, 
        nvalues_entry,
        checkbox_threshold,
        checkbox_align,
        unit_var,
        checkbox_plot,
        condition_var,
        pass_fail_var,
        file1_column_option,
        file1_listbox,
        file2_listbox,
        output_frame,
        file1_frame,
        file2_frame,
        analysis_frame,
        checkbox_event,
        start_event_var,
        end_event_var,
        file1_folder_label,
        file2_folder_label,
        start_event_option,
        end_event_option,
        event_listbox2,
        event_listbox1,
        event_filter_entry1,
        event_filter_entry2,
        unit_option_menu,
        file2_column_option_var,
        file1_column_option_var,
        checkbox_advance
    ]
    def call_reset(elements):
        """
        Clears temporary files, resets GUI widget values, and resets changed variables.
        """
        
        # 1. Remove temporary files
        files_to_remove = [
            'options_multi.txt', 'options.txt', 'options1.txt', 'options2.txt',
            'output0.csv', 'output1.csv', 'check.csv', 'data.csv', 'backup.csv',
            'backupdf2.csv', 'backupprova.csv', 'prova2.csv', 'plot.png', 'options_event.txt', 'prova1.csv', 'prova3.csv', 'prova.csv', 'output1_modified.csv','output0_modified.csv','output1check.csv','output0check.csv', 'interactive_plot.txt'
        ]
        for file in files_to_remove:
            if os.path.isfile(file):
                os.remove(file)
        
        # 2. Reset global or shared variables
        global selection_event  # e.g., your selection list used elsewhere
        selection_event = []       
        # 3. Reset each widget passed in the 'elements' list
        for element in elements:
            # Clear Entry widgets
            if isinstance(element, (tk.Entry, ctk.CTkEntry)):
                element.delete(0, tk.END)
            # Clear Listbox widgets
            elif isinstance(element, tk.Listbox):
                element.delete(0, tk.END)
            # For Labels or other widgets, reset text if desired.
            elif isinstance(element, (tk.Label, ctk.CTkLabel)):
                # Reset to an empty string or a default value if available
                element.configure(text="")
        
        # 4. Reset OptionMenus and Checkboxes via their associated variables.
        # (Make sure these variables are in scope or passed in as needed.)
        try:
            unit_var.set("N/A")
        except Exception:
            pass
        try:
            condition_var.set("x>Limit1")
        except Exception:
            pass
        try:    
            pass_fail_var.set("Fail")
        except Exception:
            pass
        try:
            end_event_var.set("End Event")
        except Exception:
            pass
        try:
            start_event_var.set("Start Event")
        except Exception:
            pass
        try:
            file1_optionmenu_var.set("Select File")
        except Exception:
            pass
        try:
            file2_optionmenu_var.set("Select File")
        except Exception:
            pass
        try:
            file2_column_option_var.set("Select Column")
        except Exception:
            pass
        try:
            file1_column_option_var.set("Select Column")
        except Exception:
            pass
        try:
            file2_folder_label.configure(text="No folder selected")
        except Exception:
            pass
        try:
            file1_folder_label.configure(text="No folder selected")
        except Exception:
            pass
        try:
            output_folder_label.configure(text="No folder selected")
        except Exception:
            pass
        
        try:
            # Reset checkbox states (if using BooleanVar)
            checkbox_threshold.set(False)
            checkbox_align.set(False)
            checkbox_plot.set(False)
            checkbox_event.set(False)
            checkbox_advance.set(False)
        except Exception:
            pass

        # 5. Call additional module reset functions if they perform extra resets
        dl.reset_gui(elements)
        st.reset_gui2(elements)
    return main_frame

# --- Main --- #
if __name__ == "__main__":
    root = ctk.CTk()
    create_gui(root)
    root.mainloop()
