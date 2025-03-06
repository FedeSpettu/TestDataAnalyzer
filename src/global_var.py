# Global variables to store state
plot_dictionary= {
}

selection = {
    'File1': [],
    'File2': []
}
selection_event = []
files_selection = []
folder_path=[]
output_path=''
output_file=''
files=[]
status='Ready'
# Track which folder is currently selected
k=-1
z=0
j=0
clean_paths = []
check_plot=0
# Tkinter trace variables
trace_id=''
trace_id1=''
# Current page number for Excel output
currentpage=0
# Minimum consecutive data rows to avoid false positives
min_data_rows = 2 

enable_plot = False