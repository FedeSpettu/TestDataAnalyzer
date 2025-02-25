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

# --- Monkey-patch NavigationToolbar2Tk.set_message to avoid thread errors ---
def safe_set_message(self, s):
    try:
        self.message.set(s)
    except RuntimeError:
        pass

NavigationToolbar2Tk.set_message = safe_set_message

# --- Custom Fast Zoom Toolbar using Blitting ---
class FastZoomToolbar2Tk(NavigationToolbar2Tk):
    """
    A custom toolbar subclass that implements a faster zoom-to-rectangle function.
    Instead of redrawing the entire canvas on every mouse movement, it uses
    blitting to only update the zoom rectangle.
    """
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
        if self.mode != 'zoom':
            return
        if event.inaxes is None:
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
        if not self._zoom_active:
            return
        if event.inaxes is None or self._zoom_rect is None or self._zoom_background is None:
            return
        ax = event.inaxes
        self.canvas.restore_region(self._zoom_background)
        x0, y0 = self._zoom_start_data
        x1, y1 = event.xdata, event.ydata
        xmin = min(x0, x1)
        ymin = min(y0, y1)
        width = abs(x1 - x0)
        height = abs(y1 - y0)
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

# --- Utility function to check for time-like columns ---
def _is_time_column(series):
    try:
        pd.to_datetime(series, format="%H:%M:%S")
        return True
    except Exception:
        return False

# --- Main Interactive Plot Application ---
class InteractivePlotApp(tk.Toplevel):
    def __init__(self, parent, df1, df2=None):
        super().__init__(parent)
        self.title("Interactive Plot")
        self.geometry("1000x700")
        print("Initializing Interactive Plot App...")

        self.df1 = df1.copy()
        if df2 is not None:
            self.df2 = df1.copy()
            self.df1 = df2.copy()
            if 'Event' in self.df2.columns:
                self.df2 = self.df2.drop('Event', axis=1)
            if 'Limit1' in self.df2.columns:
                self.df2 = self.df2.drop('Limit1', axis=1)
            if 'Limit2' in self.df2.columns:    
                self.df2 = self.df2.drop('Limit2', axis=1)
        else:
            self.df2 = None

        # Ensure the first column is time-like (hh:mm:ss).
        if not _is_time_column(self.df1.iloc[:, 0]):
            x_axis = pd.date_range(start='00:00:00', periods=len(self.df1), freq='1S').strftime('%H:%M:%S')
            self.df1.insert(0, 'Time', x_axis)
        self.time_column = self.df1.columns[0]
        self.df1_time = pd.to_datetime(self.df1[self.time_column], format="%H:%M:%S", cache=True)

        if self.df2 is not None:
            if not _is_time_column(self.df2.iloc[:, 0]):
                x_axis = pd.date_range(start='00:00:00', periods=len(self.df2), freq='1S').strftime('%H:%M:%S')
                self.df2.insert(0, 'Time', x_axis)
            self.df2_time_column = self.df2.columns[0]
            self.df2_time = pd.to_datetime(self.df2[self.df2_time_column], format="%H:%M:%S", cache=True)
        else:
            self.df2_time = None

        # Colors, thresholds, and events.
        self.colors_df1 = {}
        self.colors_df2 = {}
        self.thresholds = []
        # Now store selected events as tuples (row_index, event_name)
        self.selected_events = []  
        self.custom_events = []    # track custom events

        # Operation mode variables.
        self.data_operation = 'normal'
        self.computed_series = None
        self.common_time = None
        self.computed_label = None
        self.ma_window = None

        # For hover optimization.
        self.xy_data = []
        self.kdtree = None

        # Track columns that are currently plotted.
        self.current_df1_plotted = []
        self.current_df2_plotted = []

        # State for custom event creation.
        self.custom_event_mode = False
        self.custom_event_name = None
        self.custom_event_cid = None

        # --- Layout Setup ---
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # LEFT: Plot area.
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Title input at top.
        title_frame = ttk.Frame(left_frame)
        title_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        ttk.Label(title_frame, text="Chart Title:").pack(side=tk.LEFT, padx=5)
        self.chart_title = tk.StringVar(value="")
        self.chart_title_entry = ttk.Entry(title_frame, textvariable=self.chart_title)
        self.chart_title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.chart_title_entry.bind("<Return>", lambda e: self.create_plot())

        self.fig, self.ax = plt.subplots(figsize=(7, 5))
        self.fig.subplots_adjust(right=0.75)
        self.canvas = FigureCanvasTkAgg(self.fig, master=left_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Use the custom fast zoom toolbar.
        self.toolbar = FastZoomToolbar2Tk(self.canvas, left_frame)
        self.toolbar.update()
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # Annotation for tooltip on hover.
        self.annot = self.ax.annotate("", xy=(0, 0), xytext=(10, 10),
                                    textcoords="offset points",
                                    bbox=dict(boxstyle="round", fc="w"),
                                    arrowprops=dict(arrowstyle="->"))
        self.annot.set_visible(False)
        self.canvas.mpl_connect("motion_notify_event", self.on_hover)

        # RIGHT: Controls.
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # Listbox for DF1 columns.
        df1_frame = ttk.LabelFrame(right_frame, text="DF1 Columns")
        df1_frame.pack(fill=tk.X, pady=2)
        self.df1_listbox = tk.Listbox(df1_frame, selectmode=tk.MULTIPLE, exportselection=False, height=6)
        self.df1_listbox.pack(fill=tk.BOTH, padx=5, pady=5)
        for col in self.df1.columns:
            if col != "Event" and col != self.time_column:
                self.df1_listbox.insert(tk.END, col)

        # Listbox for DF2 columns (if available).
        if self.df2 is not None:
            df2_frame = ttk.LabelFrame(right_frame, text="DF2 Columns")
            df2_frame.pack(fill=tk.X, pady=2)
            self.df2_listbox = tk.Listbox(df2_frame, selectmode=tk.MULTIPLE, exportselection=False, height=6)
            self.df2_listbox.pack(fill=tk.BOTH, padx=5, pady=5)
            for col in self.df2.columns:
                if col != "Event" and col != self.df2_time_column:
                    self.df2_listbox.insert(tk.END, col)
        else:
            self.df2_listbox = None

        # Button to plot selected columns.
        self.plot_btn = ttk.Button(right_frame, text="Plot Selected", command=self.plot_normal)
        self.plot_btn.pack(fill=tk.X, pady=2, padx=5)

        # Button for choosing DF1 color.
        self.color_btn_df1 = ttk.Button(right_frame, text="Choose DF1 Color", command=self.choose_color_df1)
        self.color_btn_df1.pack(fill=tk.X, pady=2, padx=5)
        if self.df2 is not None:
            self.color_btn_df2 = ttk.Button(right_frame, text="Choose DF2 Color", command=self.choose_color_df2)
            self.color_btn_df2.pack(fill=tk.X, pady=2, padx=5)

        # Data operations.
        data_ops_frame = ttk.LabelFrame(right_frame, text="Data Operations (Plotted Columns)")
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

        # Thresholds.
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

        # Events.
        #print(self.df1.columns)
        #print(self.df1['Event'])
        if "Event" in self.df1.columns:
            event_frame = ttk.LabelFrame(right_frame, text="Events")
            event_frame.pack(fill=tk.X, pady=2, padx=5)           
            ttk.Label(event_frame, text="Filter Events:").pack(padx=5, pady=2)
            self.event_filter_var = tk.StringVar()
            self.event_filter_entry = ttk.Entry(event_frame, textvariable=self.event_filter_var)
            self.event_filter_entry.pack(fill=tk.X, padx=5, pady=2)
            self.event_filter_var.trace("w", lambda *args: self.filter_events())
            # Build full events list as tuples (row_index, event)
            self.all_events = [(idx, ev) for idx, ev in self.df1["Event"].dropna().items()]
            # Use a StringVar for the OptionMenu.
            self.event_option_var = tk.StringVar(event_frame)
            self.event_option_var.set("Select Event")
            formatted_events = [f"Row {idx+2}: {ev}" for idx, ev in self.all_events]
            print(formatted_events)
            self.event_option = tk.OptionMenu(event_frame, self.event_option_var, *formatted_events, command=self.add_event_from_option)
            self.event_option.pack(fill=tk.X, padx=5, pady=2)
            self.rem_event_btn = ttk.Button(event_frame, text="Remove Last Event", command=self.remove_last_event)
            self.rem_event_btn.pack(fill=tk.X, padx=5, pady=2)
            self.create_event_btn = ttk.Button(event_frame, text="Create Custom Event", command=self.initiate_custom_event)
            self.create_event_btn.pack(fill=tk.X, pady=5)
        else:
            # Create the Event column if it doesn't exist
            self.df1["Event"] = None
            event_frame = ttk.LabelFrame(right_frame, text="Events")
            event_frame.pack(fill=tk.X, pady=2, padx=5)
            
            # Since there are no events, self.all_events is empty.
            self.all_events = []
            
            # Use an OptionMenu even if it has no options.
            # First, create a StringVar and set a placeholder.
            self.event_option_var = tk.StringVar(event_frame)
            self.event_option_var.set("Select Event")
            
            # Create the OptionMenu with at least one placeholder value
            self.event_option = tk.OptionMenu(event_frame, self.event_option_var, "Select Event")
            # Remove the placeholder so that the menu appears empty.
            self.event_option["menu"].delete(0, "end")
            self.event_option.pack(fill=tk.X, padx=5, pady=2)
            
            ttk.Label(event_frame, text="Filter Events:").pack(padx=5, pady=2)
            self.event_filter_var = tk.StringVar()
            self.event_filter_entry = ttk.Entry(event_frame, textvariable=self.event_filter_var)
            self.event_filter_entry.pack(fill=tk.X, padx=5, pady=2)
            self.event_filter_var.trace("w", lambda *args: self.filter_events())
            
            self.rem_event_btn = ttk.Button(event_frame, text="Remove Last Event", 
                                            command=self.remove_last_event)
            self.rem_event_btn.pack(fill=tk.X, padx=5, pady=2)
            self.create_event_btn = ttk.Button(event_frame, text="Create Custom Event", 
                                            command=self.initiate_custom_event)
            self.create_event_btn.pack(fill=tk.X, padx=5, pady=2)

        # Final controls.
        final_frame = ttk.Frame(right_frame)
        final_frame.pack(fill=tk.X, pady=5, padx=5)
        self.save_btn = ttk.Button(final_frame, text="Append Plot to Excel", command=self.append_plot_to_excel)
        self.save_btn.pack(fill=tk.X, pady=2)
        self.close_btn = ttk.Button(final_frame, text="Close", command=self.destroy)
        self.close_btn.pack(fill=tk.X, pady=2)

        self.plot_normal()

    def format_event(self, event_tuple):
        """Helper to convert an event tuple (row_index, event_name) to a display string."""
        return f"Row {event_tuple[0]}: {event_tuple[1]}"

    def filter_events(self):
        filter_text = self.event_filter_var.get().lower()
        filtered_events = [self.format_event(ev) for ev in self.all_events if filter_text in ev[1].lower()]
        menu = self.event_option["menu"]
        menu.delete(0, "end")
        for ev_str in filtered_events:
            menu.add_command(label=ev_str, command=lambda value=ev_str: self.add_event_from_option(value))

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

        # Reset the lists of currently plotted columns.
        self.current_df1_plotted = []
        self.current_df2_plotted = []

        if self.data_operation == 'computed_difference' and self.computed_series is not None:
            self.ax.plot(self.common_time, self.computed_series, label=self.computed_label, color='green')
            self.xy_data = list(zip(self.common_time, self.computed_series))
        elif self.data_operation == 'moving_average_time' and self.ma_window is not None:
            df1_selected = [self.df1_listbox.get(idx) for idx in self.df1_listbox.curselection()]
            self.current_df1_plotted = df1_selected
            for col in df1_selected:
                t = self.df1_time
                series = self.df1[col].copy()
                series.index = t
                window_str = f"{self.ma_window}s"
                ma = series.rolling(window=window_str, min_periods=1).mean().values
                t_sec = (t - common_ref).dt.total_seconds().values
                self.ax.plot(t_sec, ma, label=f"MA Time ({self.ma_window}s): DF1:{col}", color='purple')
                self.xy_data.extend(list(zip(t_sec, ma)))
            if self.df2 is not None and self.df2_listbox is not None:
                df2_selected = [self.df2_listbox.get(idx) for idx in self.df2_listbox.curselection()]
                self.current_df2_plotted = df2_selected
                for col in df2_selected:
                    t = self.df2_time
                    series = self.df2[col].copy()
                    series.index = t
                    window_str = f"{self.ma_window}s"
                    ma = series.rolling(window=window_str, min_periods=1).mean().values
                    t_sec = (t - common_ref).dt.total_seconds().values
                    self.ax.plot(t_sec, ma, label=f"MA Time ({self.ma_window}s): DF2:{col}", color='purple')
                    self.xy_data.extend(list(zip(t_sec, ma)))
        elif self.data_operation == 'moving_average' and self.ma_window is not None:
            df1_selected = [self.df1_listbox.get(idx) for idx in self.df1_listbox.curselection()]
            self.current_df1_plotted = df1_selected
            for col in df1_selected:
                t = self.df1_time
                t_sec = (t - common_ref).dt.total_seconds().values
                ma = self.df1[col].rolling(self.ma_window, min_periods=1).mean().values
                self.ax.plot(t_sec, ma, label=f"MA ({self.ma_window}): DF1:{col}", color='blue')
                self.xy_data.extend(list(zip(t_sec, ma)))
            if self.df2 is not None and self.df2_listbox is not None:
                df2_selected = [self.df2_listbox.get(idx) for idx in self.df2_listbox.curselection()]
                self.current_df2_plotted = df2_selected
                for col in df2_selected:
                    t = self.df2_time
                    t_sec = (t - common_ref).dt.total_seconds().values
                    ma = self.df2[col].rolling(self.ma_window, min_periods=1).mean().values
                    self.ax.plot(t_sec, ma, label=f"MA ({self.ma_window}): DF2:{col}", color='blue')
                    self.xy_data.extend(list(zip(t_sec, ma)))
        else:
            df1_selected = [self.df1_listbox.get(idx) for idx in self.df1_listbox.curselection()]
            self.current_df1_plotted = df1_selected
            for col in df1_selected:
                t = self.df1_time
                t_sec = (t - common_ref).dt.total_seconds().values
                y_vals = self.df1[col].values
                color = self.colors_df1.get(col, None)
                self.ax.plot(t_sec, y_vals, label=f"DF1: {col}", color=color)
                self.xy_data.extend(list(zip(t_sec, y_vals)))
            if self.df2 is not None and self.df2_listbox is not None:
                df2_selected = [self.df2_listbox.get(idx) for idx in self.df2_listbox.curselection()]
                self.current_df2_plotted = df2_selected
                for col in df2_selected:
                    t = self.df2_time
                    t_sec = (t - common_ref).dt.total_seconds().values
                    y_vals = self.df2[col].values
                    color = self.colors_df2.get(col, None)
                    self.ax.plot(t_sec, y_vals, label=f"DF2: {col}", color=color)
                    self.xy_data.extend(list(zip(t_sec, y_vals)))

        # Draw thresholds.
        for thr in self.thresholds:
            self.ax.axhline(y=thr, color='red', linestyle='dashed', label=f"Threshold: {thr}")

        # Draw events using the stored (row_index, event) tuples.
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
            self.ax.legend(handles, labels, loc='center left', bbox_to_anchor=(1.02, 0.5))

        self.ax.set_xlabel("Elapsed Time [s]")
        self.ax.set_ylabel("Values")
        self.ax.ticklabel_format(style='plain', axis='x')
        self.ax.xaxis.get_offset_text().set_visible(False)
        self.ax.xaxis.set_major_locator(MaxNLocator(integer=True))

        if self.xy_data:
            pts = np.array(self.xy_data)
            if pts.ndim == 2 and pts.shape[1] == 2:
                self.kdtree = KDTree(pts)
            else:
                self.kdtree = None
        else:
            self.kdtree = None

        self.ax.set_title(self.chart_title.get(), pad=30)
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

    def choose_column_dialog(self, columns, prompt):
        # Create the dialog window.
        dialog = tk.Toplevel(self)
        dialog.title(prompt)
        
        # Add a label to instruct the user.
        label = tk.Label(dialog, text="Select a column:")
        label.pack(padx=10, pady=10)
        
        # Calculate the required width (in characters) based on the longest column name.
        max_length = max(len(col) for col in columns)
        combo_width = max_length + 2  # extra padding for clarity
        
        # Create a StringVar with the default (first) column.
        selected = tk.StringVar(value=columns[0])
        
        # Create the dropdown (combobox) with the computed width.
        combobox = ttk.Combobox(dialog, textvariable=selected, values=columns, state="readonly", width=combo_width)
        combobox.pack(padx=10, pady=10)
        
        result = {}
        
        # Define a callback for when the user confirms their selection.
        def on_ok():
            result["value"] = selected.get()
            dialog.destroy()
        
        # Add an OK button to confirm the selection.
        ok_button = ttk.Button(dialog, text="OK", command=on_ok)
        ok_button.pack(padx=10, pady=10)
        
        # Wait for the dialog window to close.
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
            # Clear the event at the specific row
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
                # Update the OptionMenu with the new event
                formatted_events = [self.format_event(ev) for ev in self.all_events]
                menu = self.event_option["menu"]
                menu.delete(0, "end")
                for ev_str in formatted_events:
                    menu.add_command(label=ev_str, command=lambda value=ev_str: self.add_event_from_option(value))
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
        self.ax.set_title(self.chart_title.get(), pad=30)
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
            self.ax.set_title(self.chart_title.get(), pad=30)
            buf = BytesIO()
            self.fig.savefig(buf, format='png', bbox_inches="tight", dpi=150)
            buf.seek(0)
            excel_img = ExcelImage(buf)
            excel_img.width = int(excel_img.width * (4/7))
            excel_img.height = int(excel_img.height * (4/7))
            self.fig.set_size_inches(orig_size)
            if save_full_data:
                img_cell = f"{openpyxl.utils.get_column_letter(empty_col + 2)}1"
            else:
                img_cell = f"{openpyxl.utils.get_column_letter(empty_col + 15)}1"
            ws.add_image(excel_img, img_cell)
            try:
                wb.save(file_path)
                messagebox.showinfo("Saved", f"Plot and data appended successfully to {file_path}")
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

def launch_interactive_plot(parent, df1, df2=None):
    """
    Launch the Interactive Plot Application.
    
    :param parent: Parent Tk widget.
    :param df1: Pandas DataFrame (required).
    :param df2: Pandas DataFrame (optional).
    """
    InteractivePlotApp(parent, df1, df2)
