import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from tkinter.simpledialog import askstring
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.ticker import MaxNLocator
import openpyxl
from openpyxl.drawing.image import Image as ExcelImage
from io import BytesIO
from PIL import Image
from scipy.spatial import KDTree
from matplotlib.patches import Rectangle
import os
import math
from src.usefull_functions import apply_formulas_to_column, convert_to_relative_time, align_dataframes
from datetime import datetime

def process_event(checkbox_event, df1, df2=None, options_file='options_event.txt', sec=None):
    if not checkbox_event:
        return df1, df2

    indices_event = []
    with open(options_file, 'r') as f:
        for line in f:
            parts = line.split('@#@')
            if len(parts) > 1:
                event_name = parts[1].strip()
                matching_idx = df1.index[df1['Event'] == event_name]
                if not matching_idx.empty:
                    indices_event.append(int(matching_idx.min()))
    indices_event.sort()

    if len(indices_event) == 1:
        start_event = indices_event[0]
        stop_event = df1.index[-1-int(sec)] if sec else df1.index[-1]
    elif len(indices_event) >= 2:
        start_event = indices_event[0]
        stop_event = indices_event[1]
    else:
        start_event, stop_event = df1.index[0], df1.index[-1]

    df1 = df1.iloc[start_event:stop_event+1]
    start_line = df1.iloc[0, 0]
    stop_line = df1.iloc[-1, 0]

    if df2 is not None:
        try:
            start_idx_df2 = df2.index[df2.iloc[:, 0] == start_line].tolist()[0]
        except IndexError:
            start_idx_df2 = df2.index[0]
        try:
            stop_idx_df2 = df2.index[df2.iloc[:, 0] == stop_line].tolist()[0]
        except IndexError:
            stop_idx_df2 = df2.index[-1]
        df2 = df2.iloc[start_idx_df2:stop_idx_df2+1]

    return df1, df2

def safe_set_message(self, s):
    try:
        self.message.set(s)
    except RuntimeError:
        pass

NavigationToolbar2Tk.set_message = safe_set_message

class FastZoomToolbar2Tk(NavigationToolbar2Tk):
    def __init__(self, canvas, window):
        super().__init__(canvas, window)
        self._zoom_rect = None
        self._zoom_background = None
        self._zoom_start = None
        self._zoom_start_data = None
        self._zoom_active = False
        self.canvas.mpl_connect('button_press_event', self._fast_zoom_press)
        self.canvas.mpl_connect('button_release_event', self._fast_zoom_release)
        self.canvas.mpl_connect('motion_notify_event', self._fast_zoom_motion)
    
    def _fast_zoom_press(self, event):
        if self.mode != 'zoom' or event.inaxes is None:
            return
        self._zoom_active = True
        self._zoom_start = (event.x, event.y)
        self._zoom_start_data = (event.xdata, event.ydata)
        ax = event.inaxes
        if self._zoom_rect is None:
            self._zoom_rect = Rectangle((event.xdata, event.ydata), 0, 0,
                                         fill=False, color='black', linestyle='--')
            ax.add_patch(self._zoom_rect)
        else:
            self._zoom_rect.set_visible(True)
            self._zoom_rect.set_xy((event.xdata, event.ydata))
            self._zoom_rect.set_width(0)
            self._zoom_rect.set_height(0)
        self.canvas.draw()
        self._zoom_background = self.canvas.copy_from_bbox(ax.bbox)
    
    def _fast_zoom_motion(self, event):
        if not self._zoom_active or event.inaxes is None or self._zoom_rect is None or self._zoom_background is None:
            return
        ax = event.inaxes
        self.canvas.restore_region(self._zoom_background)
        x0, y0 = self._zoom_start_data
        x1, y1 = event.xdata, event.ydata
        xmin, ymin = min(x0, x1), min(y0, y1)
        width, height = abs(x1 - x0), abs(y1 - y0)
        self._zoom_rect.set_xy((xmin, ymin))
        self._zoom_rect.set_width(width)
        self._zoom_rect.set_height(height)
        ax.draw_artist(self._zoom_rect)
        self.canvas.blit(ax.bbox)
    
    def _fast_zoom_release(self, event):
        if not self._zoom_active:
            return
        self._zoom_active = False
        if event.inaxes is None:
            return
        x0, y0 = self._zoom_start_data
        x1, y1 = event.xdata, event.ydata
        xmin, xmax = min(x0, x1), max(x0, x1)
        ymin, ymax = min(y0, y1), max(y0, y1)
        ax = event.inaxes
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        if self._zoom_rect is not None:
            self._zoom_rect.set_visible(False)
        self.canvas.draw()
        self._zoom_start = None
        self._zoom_start_data = None

def _is_time_column(series):
    try:
        pd.to_datetime(series, format="%H:%M:%S")
        return True
    except Exception:
        return False

class PaginatedOptionMenu:
    def __init__(self, master, variable, options, command=None, page_size=10):
        self.master = master
        self.variable = variable
        self.all_options = options
        self.command = command
        self.page_size = page_size
        self.current_page = 0
        self.event_option_var = tk.StringVar(master)
        self.event_option_var.set("Select Event")
        self.option_menu = tk.OptionMenu(
            master,
            self.event_option_var,
            *self.get_current_page_options(),
            command=self.on_select
        )
        self.option_menu.pack(fill=tk.X, padx=5, pady=2)
        self.event_option_var.set("Select Event")

    def get_current_page_options(self):
        start = self.current_page * self.page_size
        end = start + self.page_size
        page_options = self.all_options[start:end]
        if self.current_page > 0:
            page_options.insert(0, "< Prev")
        if end < len(self.all_options):
            page_options.append("Next >")
        return page_options

    def on_select(self, value):
        if value == "Next >":
            self.current_page += 1
            self.refresh_menu()
            x = self.option_menu.winfo_rootx()
            y = self.option_menu.winfo_rooty() + self.option_menu.winfo_height()
            self.option_menu["menu"].post(x, y)
        elif value == "< Prev":
            self.current_page -= 1
            self.refresh_menu()
            x = self.option_menu.winfo_rootx()
            y = self.option_menu.winfo_rooty() + self.option_menu.winfo_height()
            self.option_menu["menu"].post(x, y)
        else:
            if self.command:
                self.command(value)
            self.event_option_var.set("Select Event")

    def refresh_menu(self):
        new_options = self.get_current_page_options()
        menu = self.option_menu["menu"]
        menu.delete(0, "end")
        for option in new_options:
            menu.add_command(
                label=option,
                command=tk._setit(self.event_option_var, option, self.on_select)
            )
        self.event_option_var.set("Select Event")

    def update_options(self, new_options):
        self.all_options = new_options
        self.current_page = 0
        self.refresh_menu()

class InteractivePlotApp(tk.Toplevel):
    def __init__(self, parent, df1, df2=None):
        super().__init__(parent)
        self.title("Interactive Plot")
        self.geometry("1000x700")
        print("Initializing Interactive Plot App...")

        self.df1 = df1.copy()
        if df2 is not None:
            self.df2 = df2.copy()
            self.df1 = df1.copy()
            if 'Event' in self.df2.columns:
                self.df2 = self.df2.drop('Event', axis=1)
            if 'Limit1' in self.df2.columns:
                self.df2 = self.df2.drop('Limit1', axis=1)
            if 'Limit2' in self.df2.columns:    
                self.df2 = self.df2.drop('Limit2', axis=1)
        else:
            self.df2 = None

        if not _is_time_column(self.df1.iloc[:, 0]):
            x_axis = pd.date_range(start='00:00:00', periods=len(self.df1), freq='1S').strftime('%H:%M:%S')
            self.df1.insert(0, 'Time', x_axis)
        self.time_column = self.df1.columns[0]
        # Increase graph size: figure is now 15x13 inches.
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        # Set fixed margins so the title and legend areas are reserved.
        self.fig.subplots_adjust(top=0.95, bottom=0.20, right=0.95, left=0.05, hspace=0.2, wspace=0.2)
        self.df1_time = pd.to_datetime(self.df1[self.time_column], format="%H:%M:%S", cache=True)

        if self.df2 is not None:
            if not _is_time_column(self.df2.iloc[:, 0]):
                x_axis = pd.date_range(start='00:00:00', periods=len(self.df2), freq='1S').strftime('%H:%M:%S')
                self.df2.insert(0, 'Time', x_axis)
            self.df2_time_column = self.df2.columns[0]
            self.df2_time = pd.to_datetime(self.df2[self.df2_time_column], format="%H:%M:%S", cache=True)
        else:
            self.df2_time = None

        self.colors_df1 = {}
        self.colors_df2 = {}
        self.thresholds = []
        self.selected_events = []  
        self.custom_events = []

        self.data_operation = 'normal'
        self.computed_series = None
        self.common_time = None
        self.computed_label = None
        self.ma_window = None

        self.xy_data = []
        self.kdtree = None

        self.current_df1_plotted = []
        self.current_df2_plotted = []

        self.custom_event_mode = False
        self.custom_event_name = None
        self.custom_event_cid = None

        # Tooltip related attributes with delayed display
        self.listbox_tooltip = None
        self.tooltip_after_id = None
        self.tooltip_index = None
        self.tooltip_widget = None

        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # LEFT: Plot area.
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        title_frame = ttk.Frame(left_frame)
        title_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        ttk.Label(title_frame, text="Chart Title:").pack(side=tk.LEFT, padx=5)
        self.chart_title = tk.StringVar(value="")
        self.chart_title_entry = ttk.Entry(title_frame, textvariable=self.chart_title)
        self.chart_title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.chart_title_entry.bind("<Return>", lambda e: self.create_plot())

        self.canvas = FigureCanvasTkAgg(self.fig, master=left_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.toolbar = FastZoomToolbar2Tk(self.canvas, left_frame)
        self.toolbar.update()
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.annot = self.ax.annotate("", xy=(0, 0), xytext=(10, 10),
                                    textcoords="offset points",
                                    bbox=dict(boxstyle="round", fc="w"),
                                    arrowprops=dict(arrowstyle="->"))
        self.annot.set_visible(False)
        self.canvas.mpl_connect("motion_notify_event", self.on_hover)

        # RIGHT: Controls.
        right_frame = ttk.Frame(main_frame, width=300)
        right_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        right_frame.pack_propagate(False)

        # --- DF1 Columns with Filter ---
        df1_frame = ttk.LabelFrame(right_frame, text="DF1 Columns")
        df1_frame.pack(fill=tk.X, pady=2)
        df1_filter_label = ttk.Label(df1_frame, text="Filter Columns:")
        df1_filter_label.pack(fill=tk.X, padx=5, pady=2)
        self.df1_filter_var = tk.StringVar()
        self.df1_filter_entry = ttk.Entry(df1_frame, textvariable=self.df1_filter_var)
        self.df1_filter_entry.pack(fill=tk.X, padx=5, pady=2)
        self.df1_filter_entry.bind("<Return>", lambda event: self.populate_df1_listbox())
        self.df1_listbox = tk.Listbox(df1_frame, selectmode=tk.MULTIPLE, exportselection=False, height=3)
        self.df1_listbox.pack(fill=tk.BOTH, padx=5, pady=5)
        self.df1_listbox.bind("<Motion>", self.on_listbox_hover)
        self.df1_listbox.bind("<Leave>", self.on_listbox_leave)
        self.populate_df1_listbox()

        # --- DF2 Columns with Filter (if available) ---
        if self.df2 is not None:
            df2_frame = ttk.LabelFrame(right_frame, text="DF2 Columns")
            df2_frame.pack(fill=tk.X, pady=2)
            df2_filter_label = ttk.Label(df2_frame, text="Filter Columns:")
            df2_filter_label.pack(fill=tk.X, padx=5, pady=2)
            self.df2_filter_var = tk.StringVar()
            self.df2_filter_entry = ttk.Entry(df2_frame, textvariable=self.df2_filter_var)
            self.df2_filter_entry.pack(fill=tk.X, padx=5, pady=2)
            self.df2_filter_entry.bind("<Return>", lambda event: self.populate_df2_listbox())
            self.df2_listbox = tk.Listbox(df2_frame, selectmode=tk.MULTIPLE, exportselection=False, height=3)
            self.df2_listbox.pack(fill=tk.BOTH, padx=5, pady=5)
            self.df2_listbox.bind("<Motion>", self.on_listbox_hover)
            self.df2_listbox.bind("<Leave>", self.on_listbox_leave)
            self.populate_df2_listbox()
        else:
            self.df2_listbox = None

        self.plot_btn = ttk.Button(right_frame, text="Plot Selected", command=self.plot_normal)
        self.plot_btn.pack(fill=tk.X, pady=2, padx=5)

        self.color_btn_df1 = ttk.Button(right_frame, text="Choose DF1 Color", command=self.choose_color_df1)
        self.color_btn_df1.pack(fill=tk.X, pady=2, padx=5)
        if self.df2 is not None:
            self.color_btn_df2 = ttk.Button(right_frame, text="Choose DF2 Color", command=self.choose_color_df2)
            self.color_btn_df2.pack(fill=tk.X, pady=2, padx=5)

        data_ops_frame = ttk.LabelFrame(right_frame, text="Data Operations")
        data_ops_frame.pack(fill=tk.X, pady=2, padx=5)
        self.diff_btn = ttk.Button(data_ops_frame, text="Plot Difference", command=self.plot_difference)
        self.diff_btn.pack(fill=tk.X, padx=5, pady=2)
        ma_frame = ttk.Frame(data_ops_frame)
        ma_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(ma_frame, text="MA Window:").pack(side=tk.LEFT, padx=2)
        self.ma_entry = ttk.Entry(ma_frame, width=5)
        self.ma_entry.pack(side=tk.LEFT, padx=2)
        self.ma_btn = ttk.Button(data_ops_frame, text="Plot Moving Average", command=self.plot_moving_average)
        self.ma_btn.pack(fill=tk.X, padx=5, pady=2)
        self.ma_time_btn = ttk.Button(data_ops_frame, text="Plot MA (Time Window)", command=self.plot_moving_average_time)
        self.ma_time_btn.pack(fill=tk.X, padx=5, pady=2)

        thresh_frame = ttk.LabelFrame(right_frame, text="Thresholds")
        thresh_frame.pack(fill=tk.X, pady=2, padx=5)
        thresh_inner = ttk.Frame(thresh_frame)
        thresh_inner.pack(fill=tk.X, pady=2, padx=5)
        ttk.Label(thresh_inner, text="Value:").pack(side=tk.LEFT, padx=2)
        self.threshold_entry = ttk.Entry(thresh_inner, width=8)
        self.threshold_entry.pack(side=tk.LEFT, padx=2)
        self.add_thresh_btn = ttk.Button(thresh_inner, text="Add", command=self.add_threshold)
        self.add_thresh_btn.pack(side=tk.LEFT, padx=2)
        self.rem_thresh_btn = ttk.Button(thresh_inner, text="Remove Last", command=self.remove_threshold)
        self.rem_thresh_btn.pack(side=tk.LEFT, padx=2)

        if "Event" in self.df1.columns:
            event_frame = ttk.LabelFrame(right_frame, text="Events")
            event_frame.pack(fill=tk.X, pady=2, padx=5)
            
            ttk.Label(event_frame, text="Filter Events:").pack(padx=5, pady=2)
            self.event_filter_var = tk.StringVar()
            self.event_filter_entry = ttk.Entry(event_frame, textvariable=self.event_filter_var)
            self.event_filter_entry.pack(fill=tk.X, padx=5, pady=2)
            self.event_filter_entry.bind("<Return>", lambda event: self.filter_events())
            self.all_events = [(idx, ev) for idx, ev in self.df1["Event"].dropna().items()]
            self.event_option_var = tk.StringVar(event_frame)
            self.event_option_var.set("Select Event")
            formatted_events = [f"Row {idx+2}: {ev}" for idx, ev in self.all_events]
            self.event_menu = PaginatedOptionMenu(event_frame, self.event_option_var, formatted_events,
                                                   command=self.add_event_from_option, page_size=10)
            
            self.rem_event_btn = ttk.Button(event_frame, text="Remove Last Event", command=self.remove_last_event)
            self.rem_event_btn.pack(fill=tk.X, padx=5, pady=2)
            self.create_event_btn = ttk.Button(event_frame, text="Create Custom Event", command=self.initiate_custom_event)
            self.create_event_btn.pack(fill=tk.X, pady=5)
        else:
            self.df1["Event"] = None
            event_frame = ttk.LabelFrame(right_frame, text="Events")
            event_frame.pack(fill=tk.X, pady=2, padx=5)
            
            self.all_events = []
            
            ttk.Label(event_frame, text="Filter Events:").pack(padx=5, pady=2)
            self.event_filter_var = tk.StringVar()
            self.event_filter_entry = ttk.Entry(event_frame, textvariable=self.event_filter_var)
            self.event_filter_entry.pack(fill=tk.X, padx=5, pady=2)
            self.event_filter_entry.bind("<KeyRelease>", lambda event: self.filter_events())

            self.event_option_var = tk.StringVar(event_frame)
            self.event_option_var.set("Select Event")
            
            self.event_menu = PaginatedOptionMenu(event_frame, self.event_option_var, ["Select Event"],
                                                   command=self.add_event_from_option, page_size=10)
            
            self.rem_event_btn = ttk.Button(event_frame, text="Remove Last Event", 
                                            command=self.remove_last_event)
            self.rem_event_btn.pack(fill=tk.X, padx=5, pady=2)
            self.create_event_btn = ttk.Button(event_frame, text="Create Custom Event", 
                                            command=self.initiate_custom_event)
            self.create_event_btn.pack(fill=tk.X, padx=5, pady=2)

        final_frame = ttk.Frame(right_frame)
        final_frame.pack(fill=tk.X, pady=5, padx=5)
        self.save_btn = ttk.Button(final_frame, text="Append Plot to Excel", command=self.append_plot_to_excel)
        self.save_btn.pack(fill=tk.X, pady=2)
        self.close_btn = ttk.Button(final_frame, text="Close", command=self.destroy)
        self.close_btn.pack(fill=tk.X, pady=2)

        self.plot_normal()

    def populate_df1_listbox(self):
        self.df1_listbox.delete(0, tk.END)
        filter_text = self.df1_filter_entry.get().strip().lower()
        for col in self.df1.columns:
            if col not in ["Event", self.time_column]:
                if filter_text in col.lower():
                    self.df1_listbox.insert(tk.END, col)
                    
    def populate_df2_listbox(self):
        self.df2_listbox.delete(0, tk.END)
        filter_text = self.df2_filter_entry.get().strip().lower()
        for col in self.df2.columns:
            if col not in ["Event", self.df2_time_column]:
                if filter_text in col.lower():
                    self.df2_listbox.insert(tk.END, col)

    def filter_events(self):
        filter_text = self.event_filter_entry.get().strip().lower()
        filtered_events = [self.format_event(ev) for ev in self.all_events if filter_text in self.format_event(ev).lower()]
        self.event_menu.update_options(filtered_events)

    def format_event(self, event_tuple):
        return f"Row {event_tuple[0]}: {event_tuple[1]}"

    def add_event_from_option(self, selected):
        if not selected or selected == "Select Event":
            return
        try:
            parts = selected.split(": ", 1)
            row_str = parts[0].replace("Row ", "")
            row_idx = int(row_str)
            ev_name = parts[1]
        except Exception:
            return
        event_tuple = (row_idx, ev_name)
        if event_tuple not in self.selected_events:
            self.selected_events.append(event_tuple)
            self.event_option_var.set("Select Event")
            self.create_plot()

    def get_common_reference(self):
        t1 = self.df1_time
        if self.df2 is not None:
            t2 = self.df2_time
            return min(t1.min(), t2.min())
        else:
            return t1.min()

    def create_plot(self):
        self.ax.clear()
        self.xy_data = []
        common_ref = self.get_common_reference()
        default_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

        self.current_df1_plotted = []
        self.current_df2_plotted = []

        if self.data_operation == 'computed_difference' and self.computed_series is not None:
            try:
                self.ax.plot(self.common_time, self.computed_series, label=self.computed_label, color='green')
                self.xy_data = list(zip(self.common_time, self.computed_series))
            except Exception as e:
                messagebox.showerror("Plot Error", f"Error plotting computed difference: {e}")
        elif self.data_operation == 'moving_average_time' and self.ma_window is not None:
            df1_selected = [self.df1_listbox.get(idx) for idx in self.df1_listbox.curselection()]
            self.current_df1_plotted = df1_selected
            for i, col in enumerate(df1_selected):
                try:
                    t = self.df1_time
                    series = self.df1[col].copy()
                    series.index = t
                    window_str = f"{self.ma_window}s"
                    ma = series.rolling(window=window_str, min_periods=1).mean().values
                    t_sec = (t - common_ref).dt.total_seconds().values
                    color = self.colors_df1.get(col, default_colors[i % len(default_colors)])
                    self.ax.plot(t_sec, ma, label=f"MA Time ({self.ma_window}s): DF1:{col}", color=color)
                    self.xy_data.extend(list(zip(t_sec, ma)))
                except Exception as e:
                    messagebox.showerror("Plot Error", f"Column '{col}' could not be plotted (MA Time, DF1): {e}")
                    continue
            if self.df2 is not None and self.df2_listbox is not None:
                df2_selected = [self.df2_listbox.get(idx) for idx in self.df2_listbox.curselection()]
                self.current_df2_plotted = df2_selected
                for i, col in enumerate(df2_selected):
                    try:
                        t = self.df2_time
                        series = self.df2[col].copy()
                        series.index = t
                        window_str = f"{self.ma_window}s"
                        ma = series.rolling(window=window_str, min_periods=1).mean().values
                        t_sec = (t - common_ref).dt.total_seconds().values
                        color = self.colors_df2.get(col, default_colors[i % len(default_colors)])
                        self.ax.plot(t_sec, ma, label=f"MA Time ({self.ma_window}s): DF2:{col}", color=color)
                        self.xy_data.extend(list(zip(t_sec, ma)))
                    except Exception as e:
                        messagebox.showerror("Plot Error", f"Column '{col}' could not be plotted (MA Time, DF2): {e}")
                        continue
        elif self.data_operation == 'moving_average' and self.ma_window is not None:
            df1_selected = [self.df1_listbox.get(idx) for idx in self.df1_listbox.curselection()]
            self.current_df1_plotted = df1_selected
            for i, col in enumerate(df1_selected):
                try:
                    t = self.df1_time
                    t_sec = (t - common_ref).dt.total_seconds().values
                    ma = self.df1[col].rolling(self.ma_window, min_periods=1).mean().values
                    color = self.colors_df1.get(col, default_colors[i % len(default_colors)])
                    self.ax.plot(t_sec, ma, label=f"MA ({self.ma_window}): DF1:{col}", color=color)
                    self.xy_data.extend(list(zip(t_sec, ma)))
                except Exception as e:
                    messagebox.showerror("Plot Error", f"Column '{col}' could not be plotted (MA, DF1): {e}")
                    continue
            if self.df2 is not None and self.df2_listbox is not None:
                df2_selected = [self.df2_listbox.get(idx) for idx in self.df2_listbox.curselection()]
                self.current_df2_plotted = df2_selected
                for col in df2_selected:
                    try:
                        t = self.df2_time
                        t_sec = (t - common_ref).dt.total_seconds().values
                        ma = self.df2[col].rolling(self.ma_window, min_periods=1).mean().values
                        color = self.colors_df2.get(col, default_colors[i % len(default_colors)])
                        self.ax.plot(t_sec, ma, label=f"MA ({self.ma_window}): DF2:{col}", color=color)
                        self.xy_data.extend(list(zip(t_sec, ma)))
                    except Exception as e:
                        messagebox.showerror("Plot Error", f"Column '{col}' could not be plotted (MA, DF2): {e}")
                        continue
        else:
            df1_selected = [self.df1_listbox.get(idx) for idx in self.df1_listbox.curselection()]
            self.current_df1_plotted = df1_selected
            for col in df1_selected:
                try:
                    t = self.df1_time
                    t_sec = (t - common_ref).dt.total_seconds().values
                    y_vals = self.df1[col].values
                    color = self.colors_df1.get(col, None)
                    self.ax.plot(t_sec, y_vals, label=f"DF1: {col}", color=color)
                    self.xy_data.extend(list(zip(t_sec, y_vals)))
                except Exception as e:
                    messagebox.showerror("Plot Error", f"Column '{col}' could not be plotted (DF1): {e}")
                    continue
            if self.df2 is not None and self.df2_listbox is not None:
                df2_selected = [self.df2_listbox.get(idx) for idx in self.df2_listbox.curselection()]
                self.current_df2_plotted = df2_selected
                for col in df2_selected:
                    try:
                        t = self.df2_time
                        t_sec = (t - common_ref).dt.total_seconds().values
                        y_vals = self.df2[col].values
                        color = self.colors_df2.get(col, None)
                        self.ax.plot(t_sec, y_vals, label=f"DF2: {col}", color=color)
                        self.xy_data.extend(list(zip(t_sec, y_vals)))
                    except Exception as e:
                        messagebox.showerror("Plot Error", f"Column '{col}' could not be plotted (DF2): {e}")
                        continue

        for thr in self.thresholds:
            self.ax.axhline(y=thr, color='red', linestyle='dashed', label=f"Threshold: {thr}")

        event_handles = []
        if "Event" in self.df1.columns and self.selected_events:
            cmap = plt.get_cmap("tab10")
            for i, event_info in enumerate(self.selected_events):
                row_idx, ev_name = event_info
                color = cmap(i % 10)
                try:
                    row_time = pd.to_datetime(self.df1.loc[row_idx, self.time_column], format="%H:%M:%S")
                except Exception:
                    continue
                ev_sec = (row_time - common_ref).total_seconds()
                self.ax.axvline(x=ev_sec, color=color, linestyle='dotted')
                event_handles.append(plt.Line2D([], [], color=color, linestyle='dotted', label=f"{ev_name} (Row {row_idx})"))
        handles, labels = self.ax.get_legend_handles_labels()
        if event_handles:
            handles.extend(event_handles)
            labels.extend([h.get_label() for h in event_handles])
        if handles:
            # Reverse the order so the first added item appears at the top.
            handles = handles[::-1]
            labels = labels[::-1]
            # If more than 10 entries, show only the first 10 (max 5 per column in 2 columns).
            if len(labels) > 10:
                handles = handles[:10]
                labels = labels[:10]
            ncol = 1 if len(labels) <= 5 else 2
            # For two columns, place the legend below the chart, centered with increased column spacing.
            if ncol == 2:
                self.ax.legend(handles, labels, loc='upper left', bbox_to_anchor=(-0.05, -0.08), ncol=ncol, columnspacing=2.0)
            else:
                self.ax.legend(handles, labels, loc='upper left', bbox_to_anchor=(-0.05, -0.08))

        self.ax.set_xlabel("Elapsed Time [s]")
        self.ax.set_ylabel("Values")
        self.ax.ticklabel_format(style='plain', axis='x')
        self.ax.xaxis.get_offset_text().set_visible(False)
        self.ax.xaxis.set_major_locator(MaxNLocator(integer=True))

        if self.xy_data:
            pts = np.array(self.xy_data)
            if pts.ndim == 2 and pts.shape[1] == 2:
                try:
                    self.kdtree = KDTree(pts)
                except ValueError:
                    self.kdtree = None
                    messagebox.showerror("Plot Error", "Column not plottable.")
                    return
            else:
                self.kdtree = None
        else:
            self.kdtree = None

        # Set the chart title with sufficient pad.
        self.ax.set_title(self.chart_title_entry.get(), pad=15)
        self.canvas.draw()

    def on_hover(self, event):
        if event.inaxes != self.ax or self.kdtree is None:
            if self.annot.get_visible():
                self.annot.set_visible(False)
                self.canvas.draw_idle()
            return

        query_point = (event.xdata, event.ydata)
        dist, idx = self.kdtree.query(query_point)
        tolerance = 10
        if dist < tolerance:
            pts = np.array(self.xy_data)
            x_val, y_val = pts[idx]
            self.annot.xy = (x_val, y_val)
            self.annot.set_text(f"x={x_val:.2f}\ny={y_val:.2f}")
            self.annot.set_visible(True)
            self.canvas.draw_idle()
        else:
            if self.annot.get_visible():
                self.annot.set_visible(False)
                self.canvas.draw_idle()

    # Tooltip methods with 2-second delay:
    def on_listbox_hover(self, event):
        listbox = event.widget
        index = listbox.nearest(event.y)
        if index < 0 or index >= listbox.size():
            self.cancel_tooltip()
            return
        current_text = listbox.get(index)
        if self.tooltip_index == index and self.listbox_tooltip is not None:
            tooltip_width = self.tooltip_label.winfo_reqwidth()
            new_x = event.x_root - tooltip_width - 10
            new_y = event.y_root
            self.listbox_tooltip.wm_geometry(f"+{new_x}+{new_y}")
            return
        else:
            self.cancel_tooltip()
            self.tooltip_index = index
            self.tooltip_widget = listbox
            self.tooltip_after_id = listbox.after(2000, lambda: self.show_tooltip(listbox, current_text, event.x_root, event.y_root))

    def show_tooltip(self, listbox, text, x, y):
        self.listbox_tooltip = tk.Toplevel(listbox)
        self.listbox_tooltip.wm_overrideredirect(True)
        self.listbox_tooltip.attributes("-topmost", True)
        self.tooltip_label = tk.Label(self.listbox_tooltip, text=text, background="white",
                                      foreground="black", relief="solid", borderwidth=1)
        self.tooltip_label.pack()
        self.listbox_tooltip.update_idletasks()
        tooltip_width = self.tooltip_label.winfo_reqwidth()
        new_x = x - tooltip_width - 10
        new_y = y
        self.listbox_tooltip.wm_geometry(f"+{new_x}+{new_y}")

    def cancel_tooltip(self):
        if self.tooltip_after_id is not None:
            if self.tooltip_widget is not None:
                self.tooltip_widget.after_cancel(self.tooltip_after_id)
            self.tooltip_after_id = None
            self.tooltip_index = None
        if self.listbox_tooltip is not None:
            self.listbox_tooltip.destroy()
            self.listbox_tooltip = None
            self.tooltip_index = None

    def on_listbox_leave(self, event):
        self.cancel_tooltip()

    def choose_column_dialog(self, columns, prompt):
        dialog = tk.Toplevel(self)
        dialog.title(prompt)
        label = tk.Label(dialog, text="Select a column:")
        label.pack(padx=10, pady=10)
        max_length = max(len(col) for col in columns)
        combo_width = max_length + 2
        selected = tk.StringVar(value=columns[0])
        combobox = ttk.Combobox(dialog, textvariable=selected, values=columns, state="readonly", width=combo_width)
        combobox.pack(padx=10, pady=10)
        result = {}
        def on_ok():
            result["value"] = selected.get()
            dialog.destroy()
        ok_button = ttk.Button(dialog, text="OK", command=on_ok)
        ok_button.pack(padx=10, pady=10)
        dialog.wait_window()
        return result.get("value")

    def choose_color_df1(self):
        if not self.current_df1_plotted:
            messagebox.showwarning("No Plotted Column", "No columns are currently plotted.")
            return
        if len(self.current_df1_plotted) == 1:
            column = self.current_df1_plotted[0]
        else:
            column = self.choose_column_dialog(self.current_df1_plotted, "Select Column")
            if not column:
                return
        color = colorchooser.askcolor()[1]
        if color:
            self.colors_df1[column] = color
            self.create_plot()

    def choose_color_df2(self):
        if not self.current_df2_plotted:
            messagebox.showwarning("No Plotted Column", "No DF2 columns are currently plotted.")
            return
        if len(self.current_df2_plotted) == 1:
            column = self.current_df2_plotted[0]
        else:
            column = self.choose_column_dialog(self.current_df2_plotted, "Select DF2 Column")
            if not column:
                return
        color = colorchooser.askcolor()[1]
        if color:
            self.colors_df2[column] = color
            self.create_plot()

    def add_threshold(self):
        value = self.threshold_entry.get().strip()
        if not value:
            messagebox.showwarning("Input Error", "Threshold entry is empty.")
            return
        try:
            thr = float(value)
            self.thresholds.append(thr)
            self.threshold_entry.delete(0, tk.END)
            self.create_plot()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for threshold.")

    def remove_threshold(self):
        if self.thresholds:
            self.thresholds.pop()
            self.create_plot()
        else:
            messagebox.showinfo("Remove Threshold", "No thresholds to remove.")

    def remove_last_event(self):
        if self.selected_events:
            rem = self.selected_events.pop()
            self.df1.loc[rem[0], "Event"] = None
            if rem in self.custom_events:
                self.custom_events.remove(rem)
            self.create_plot()
        else:
            messagebox.showinfo("Remove Event", "No events to remove.")

    def initiate_custom_event(self):
        custom_event = askstring("Custom Event", "Enter custom event name:")
        if custom_event:
            self.custom_event_mode = True
            self.custom_event_name = custom_event
            if custom_event not in [ev[1] for ev in self.custom_events]:
                self.custom_events.append(custom_event)
            messagebox.showinfo("Custom Event", "Click on the chart to add the event.")
            self.custom_event_cid = self.canvas.mpl_connect("button_press_event", self.on_custom_event_click)

    def on_custom_event_click(self, event):
        if self.custom_event_mode and event.inaxes == self.ax:
            common_ref = self.get_common_reference()
            t_sec = (self.df1_time - common_ref).dt.total_seconds()
            idx = (np.abs(t_sec - event.xdata)).idxmin()
            self.df1.loc[idx, "Event"] = self.custom_event_name
            event_tuple = (idx+2, self.custom_event_name)
            if event_tuple not in self.all_events:
                self.all_events.append(event_tuple)
                formatted_events = [self.format_event(ev) for ev in self.all_events]
                self.event_menu.update_options(formatted_events)
            if event_tuple not in self.selected_events:
                self.selected_events.append(event_tuple)
            messagebox.showinfo("Custom Event", f"Event '{self.custom_event_name}' added at time {self.df1.loc[idx, self.time_column]}")
            self.canvas.mpl_disconnect(self.custom_event_cid)
            self.custom_event_mode = False
            self.create_plot()

    def plot_difference(self):
        self.data_operation = 'computed_difference'
        selections = []
        selections.extend([("DF1", self.df1_listbox.get(idx)) for idx in self.df1_listbox.curselection()])
        if self.df2_listbox is not None:
            selections.extend([("DF2", self.df2_listbox.get(idx)) for idx in self.df2_listbox.curselection()])
        if len(selections) != 2:
            messagebox.showerror("Plot Difference", "Select exactly two columns (from DF1 and/or DF2) for difference.")
            self.data_operation = 'normal'
            return

        src1, col1 = selections[0]
        src2, col2 = selections[1]
        series1 = self.df1[col1] if src1 == "DF1" else self.df2[col1]
        series2 = self.df1[col2] if src2 == "DF1" else self.df2[col2]
        t1 = self.df1_time if src1 == "DF1" else self.df2_time
        t2 = self.df1_time if src2 == "DF1" else self.df2_time
        common_ref = min(t1.min(), t2.min())
        t1_sec = (t1 - common_ref).dt.total_seconds().values
        t2_sec = (t2 - common_ref).dt.total_seconds().values
        common_time = np.union1d(t1_sec, t2_sec)
        interp1 = np.interp(common_time, t1_sec, series1.values)
        interp2 = np.interp(common_time, t2_sec, series2.values)
        self.computed_series = interp1 - interp2
        self.common_time = common_time
        self.computed_label = f"Difference: {src1}:{col1} - {src2}:{col2}"
        self.create_plot()

    def plot_moving_average(self):
        self.data_operation = 'moving_average'
        selections = []
        selections.extend([("DF1", self.df1_listbox.get(idx)) for idx in self.df1_listbox.curselection()])
        if self.df2_listbox is not None:
            selections.extend([("DF2", self.df2_listbox.get(idx)) for idx in self.df2_listbox.curselection()])
        if not selections:
            messagebox.showerror("Moving Average", "Select at least one column for moving average.")
            self.data_operation = 'normal'
            return
        try:
            window = int(self.ma_entry.get().strip())
            if window < 1:
                raise ValueError
            self.ma_window = window
        except ValueError:
            messagebox.showerror("Moving Average", "Enter a valid positive integer for the window.")
            self.data_operation = 'normal'
            return
        self.create_plot()

    def plot_moving_average_time(self):
        self.data_operation = 'moving_average_time'
        selections = []
        selections.extend([("DF1", self.df1_listbox.get(idx)) for idx in self.df1_listbox.curselection()])
        if self.df2_listbox is not None:
            selections.extend([("DF2", self.df2_listbox.get(idx)) for idx in self.df2_listbox.curselection()])
        if not selections:
            messagebox.showerror("Moving Average (Time)", "Select at least one column for moving average by time window.")
            self.data_operation = 'normal'
            return
        try:
            window_sec = float(self.ma_entry.get().strip())
            if window_sec <= 0:
                raise ValueError
            self.ma_window = window_sec
        except ValueError:
            messagebox.showerror("Moving Average (Time)", "Enter a valid positive number for the time window (in seconds).")
            self.data_operation = 'normal'
            return
        self.create_plot()

    def save_plot_to_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                filetypes=[("Excel files", "*.xlsx")])
        if not file_path:
            return
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Plot"
        start_row = ws.max_row + 1 if ws["A1"].value is not None else 1

        if self.data_operation in ['computed_difference', 'moving_average', 'moving_average_time']:
            if self.data_operation == 'computed_difference' and self.computed_series is not None:
                result_df = pd.DataFrame({self.time_column: self.df1[self.time_column], self.computed_label: self.computed_series})
            elif self.data_operation == 'moving_average':
                result_df = pd.DataFrame({self.time_column: self.df1[self.time_column]})
                df1_selected = [self.df1_listbox.get(idx) for idx in self.df1_listbox.curselection()]
                for col in df1_selected:
                    ma = self.df1[col].rolling(self.ma_window, min_periods=1).mean()
                    result_df[f"MA ({self.ma_window}): DF1:{col}"] = ma
                if self.df2 is not None and self.df2_listbox is not None:
                    df2_selected = [self.df2_listbox.get(idx) for idx in self.df2_listbox.curselection()]
                    for col in df2_selected:
                        ma = self.df2[col].rolling(self.ma_window, min_periods=1).mean()
                        result_df[f"MA ({self.ma_window}): DF2:{col}"] = ma
            elif self.data_operation == 'moving_average_time':
                result_df = pd.DataFrame({self.time_column: self.df1[self.time_column]})
                df1_selected = [self.df1_listbox.get(idx) for idx in self.df1_listbox.curselection()]
                for col in df1_selected:
                    t = self.df1_time
                    series = self.df1[col].copy()
                    series.index = t
                    window_str = f"{self.ma_window}s"
                    ma = series.rolling(window=window_str, min_periods=1).mean()
                    result_df[f"MA Time ({self.ma_window}s): DF1:{col}"] = ma
                if self.df2 is not None and self.df2_listbox is not None:
                    df2_selected = [self.df2_listbox.get(idx) for idx in self.df2_listbox.curselection()]
                    for col in df2_selected:
                        t = self.df2_time
                        series = self.df2[col].copy()
                        series.index = t
                        window_str = f"{self.ma_window}s"
                        ma = series.rolling(window=window_str, min_periods=1).mean()
                        result_df[f"MA Time ({self.ma_window}s): DF2:{col}"] = ma
            if "Event" in self.df1.columns:
                result_df["Event"] = self.df1["Event"]
            for c_idx, header in enumerate(result_df.columns, start=1):
                ws.cell(row=start_row, column=c_idx, value=header)
            for r_idx, row in enumerate(result_df.itertuples(index=False), start=start_row+1):
                for c_idx, value in enumerate(row, start=1):
                    ws.cell(row=r_idx, column=c_idx, value=value)
            start_row = start_row + result_df.shape[0] + 2
        else:
            df_to_save = pd.DataFrame({self.time_column: pd.to_datetime(self.df1[self.time_column], format="%H:%M:%S").dt.strftime('%H:%M:%S')})
            df1_selected = [self.df1_listbox.get(idx) for idx in self.df1_listbox.curselection()]
            for col in df1_selected:
                df_to_save[f"DF1: {col}"] = self.df1[col]
            if self.df2 is not None and self.df2_listbox is not None:
                df2_selected = [self.df2_listbox.get(idx) for idx in self.df2_listbox.curselection()]
                for col in df2_selected:
                    df_to_save[f"DF2: {col}"] = self.df2[col]
            if "Event" in self.df1.columns:
                df_to_save["Event"] = self.df1["Event"]
            for c_idx, header in enumerate(df_to_save.columns, start=1):
                ws.cell(row=1, column=c_idx, value=header)
            for r_idx, row in enumerate(df_to_save.itertuples(index=False), start=2):
                for c_idx, value in enumerate(row, start=1):
                    ws.cell(row=r_idx, column=c_idx, value=value)

        headers = [cell.value for cell in ws[1]]
        if "Event" in headers:
            event_col_index = headers.index("Event") + 1
            ws.delete_cols(event_col_index)
        new_event_col = ws.max_column + 1
        ws.cell(row=1, column=new_event_col, value="Event")
        num_rows = ws.max_row
        for r in range(2, num_rows+1):
            if r-2 < len(self.df1):
                event_val = self.df1.iloc[r-2].get("Event", None)
            else:
                event_val = None
            ws.cell(row=r, column=new_event_col, value=event_val)

        orig_size = self.fig.get_size_inches()
        new_size = orig_size * (4/7)
        self.fig.set_size_inches(new_size)
        self.ax.set_title(self.chart_title_entry.get(), pad=15)
        buf = BytesIO()
        self.fig.savefig(buf, format='png', bbox_inches="tight", dpi=150)
        buf.seek(0)
        excel_img = ExcelImage(buf)
        self.fig.set_size_inches(orig_size)
        img_cell = f"{openpyxl.utils.get_column_letter(ws.max_column + 2)}1"
        ws.add_image(excel_img, img_cell)
        try:
            wb.save(file_path)
            messagebox.showinfo("Saved", f"Plot (and computed data if applicable) saved successfully to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save to Excel file: {e}")
        finally:
            buf.close()

    def append_plot_to_excel(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if not file_path:
            return

        try:
            wb = openpyxl.load_workbook(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open Excel file: {e}")
            return

        sheet_dialog = tk.Toplevel(self)
        sheet_dialog.title("Select or Create Sheet")
        sheet_dialog.geometry("350x200")
        content_frame = ttk.Frame(sheet_dialog)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        confirm_frame = ttk.Frame(sheet_dialog)
        confirm_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        sheet_var = tk.StringVar()
        new_sheet_var = tk.StringVar()

        select_frame = ttk.Frame(content_frame)
        select_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(select_frame, text="Select existing sheet:").pack(pady=5)
        sheet_dropdown = ttk.Combobox(select_frame, textvariable=sheet_var, values=wb.sheetnames, state="readonly")
        sheet_dropdown.pack(pady=5)
        sheet_dropdown.set(wb.sheetnames[0])
        add_page_btn = ttk.Button(select_frame, text="Add New Page", command=lambda: switch_to_new_sheet())
        add_page_btn.pack(pady=5)

        new_sheet_frame = ttk.Frame(content_frame)
        back_btn = ttk.Button(new_sheet_frame, text="← Back to Selection", command=lambda: switch_to_existing_sheet())
        back_btn.pack(pady=5, anchor="w")
        ttk.Label(new_sheet_frame, text="Enter new sheet name:").pack(pady=5)
        new_sheet_entry = ttk.Entry(new_sheet_frame, textvariable=new_sheet_var)
        new_sheet_entry.pack(pady=5)

        def switch_to_new_sheet():
            select_frame.pack_forget()
            new_sheet_frame.pack(fill=tk.BOTH, expand=True)

        def switch_to_existing_sheet():
            new_sheet_frame.pack_forget()
            select_frame.pack(fill=tk.BOTH, expand=True)

        def on_confirm():
            if new_sheet_frame.winfo_ismapped():
                new_sheet_name = new_sheet_var.get().strip()
                if not new_sheet_name:
                    messagebox.showerror("Error", "Please enter a sheet name.")
                    return
                if new_sheet_name in wb.sheetnames:
                    messagebox.showerror("Error", "Sheet name already exists. Choose another name.")
                    return
                ws = wb.create_sheet(title=new_sheet_name)
                save_full_data = True
            else:
                selected_sheet = sheet_var.get().strip()
                ws = wb[selected_sheet]
                save_full_data = False
            sheet_dialog.destroy()

            max_col = ws.max_column
            empty_col = max_col + 2

            formatted_time = pd.to_datetime(self.df1[self.time_column], format="%H:%M:%S").dt.strftime('%H:%M:%S')

            if save_full_data:
                df_to_save = pd.DataFrame({self.time_column: formatted_time})
                df1_selected = [self.df1_listbox.get(idx) for idx in self.df1_listbox.curselection()]
                for col in df1_selected:
                    df_to_save[f"DF1: {col}"] = self.df1[col]
                if self.df2 is not None and self.df2_listbox is not None:
                    df2_selected = [self.df2_listbox.get(idx) for idx in self.df2_listbox.curselection()]
                    for col in df2_selected:
                        df_to_save[f"DF2: {col}"] = self.df2[col]
                if "Event" in self.df1.columns:
                    df_to_save["Event"] = self.df1["Event"]
                for c_idx, header in enumerate(df_to_save.columns, start=1):
                    ws.cell(row=1, column=c_idx, value=header)
                for r_idx, row in enumerate(df_to_save.itertuples(index=False), start=2):
                    for c_idx, value in enumerate(row, start=1):
                        ws.cell(row=r_idx, column=c_idx, value=value)
            else:
                result_df = pd.DataFrame()
                if self.data_operation == 'computed_difference' and self.computed_series is not None:
                    result_df[self.computed_label] = self.computed_series
                elif self.data_operation == 'moving_average':
                    df1_selected = [self.df1_listbox.get(idx) for idx in self.df1_listbox.curselection()]
                    for col in df1_selected:
                        ma = self.df1[col].rolling(self.ma_window, min_periods=1).mean()
                        result_df[f"MA ({self.ma_window}): DF1:{col}"] = ma
                elif self.data_operation == 'moving_average_time':
                    df1_selected = [self.df1_listbox.get(idx) for idx in self.df1_listbox.curselection()]
                    for col in df1_selected:
                        t = self.df1_time
                        series = self.df1[col].copy()
                        series.index = t
                        window_str = f"{self.ma_window}s"
                        ma = series.rolling(window=window_str, min_periods=1).mean()
                        result_df[f"MA Time ({self.ma_window}s): DF1:{col}"] = ma

                start_row = 1
                for c_idx, header in enumerate(result_df.columns, start=1):
                    ws.cell(row=start_row, column=empty_col + c_idx, value=header)
                for r_idx, row in enumerate(result_df.itertuples(index=False), start=start_row+1):
                    for c_idx, value in enumerate(row, start=1):
                        ws.cell(row=r_idx, column=empty_col + c_idx, value=value)

            headers = [cell.value for cell in ws[1]]
            if "Event" in headers:
                event_col_index = headers.index("Event") + 1
                ws.delete_cols(event_col_index)
            new_event_col = ws.max_column + 1
            ws.cell(row=1, column=new_event_col, value="Event")
            num_rows = ws.max_row
            for r in range(2, num_rows+1):
                if r-2 < len(self.df1):
                    event_val = self.df1.iloc[r-2].get("Event", None)
                else:
                    event_val = None
                ws.cell(row=r, column=new_event_col, value=event_val)

            orig_size = self.fig.get_size_inches()
            new_size = orig_size * (4/7)
            self.fig.set_size_inches(new_size)
            self.ax.set_title(self.chart_title_entry.get(), pad=15)
            buf = BytesIO()
            self.fig.savefig(buf, format='png', bbox_inches="tight", dpi=150)
            buf.seek(0)
            excel_img = ExcelImage(buf)
            self.fig.set_size_inches(orig_size)
            img_cell = f"{openpyxl.utils.get_column_letter(ws.max_column + 2)}1"
            ws.add_image(excel_img, img_cell)
            try:
                wb.save(file_path)
                messagebox.showinfo("Saved", f"Plot (and computed data if applicable) saved successfully to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to append to Excel file: {e}")
            finally:
                buf.close()

        confirm_button = ttk.Button(confirm_frame, text="Confirm", command=on_confirm)
        confirm_button.pack(pady=10)

    def plot_normal(self):
        self.data_operation = 'normal'
        self.computed_series = None
        self.common_time = None
        self.ma_window = None
        self.create_plot()

def rapid_analysis(main_frame, checkbox_align, start_time1_entry, start_time2_entry, checkbox_event):
    if os.path.isfile('output0.csv'):
        df1 = pd.read_csv('output0.csv')
    else:  
        messagebox.showerror("Error", "No data found")
        return
    if os.path.isfile('output1.csv'):
        df2 = pd.read_csv('output1.csv')
    
    if checkbox_align:
        ref_time1 = pd.to_datetime(start_time1_entry.get(), format='%H:%M:%S')
        column_date1 = df1.columns[0]
        df1 = apply_formulas_to_column(df1, ref_time1, column_date1)
        
        if os.path.isfile('output1.csv'):
            ref_time2 = pd.to_datetime(start_time2_entry.get(), format='%H:%M:%S')
            column_date2 = df2.columns[0]
            df2 = apply_formulas_to_column(df2, ref_time2, column_date2) 
            df1, df2, delta_sec = align_dataframes(df1, df2, column_date1, column_date2)
            df1, df2 = process_event(checkbox_event, df1, df2=df2, options_file='options_event.txt', sec=delta_sec)
            launch_interactive_plot(main_frame, df1, df2=df2)
        else:
            df1 = process_event(checkbox_event, df1, df2=None, options_file='options_event.txt', sec=None)
            launch_interactive_plot(main_frame, df1, df2=None)
    else:
        ref_time1 = pd.to_datetime(start_time1_entry.get(), format='%H:%M:%S')
        column_date1 = df1.columns[0]
        df1 = apply_formulas_to_column(df1, ref_time1, column_date1)
        launch_interactive_plot(main_frame, df1, df2=None)
        
def launch_interactive_plot(parent, df1, df2=None):
    InteractivePlotApp(parent, df1, df2)
