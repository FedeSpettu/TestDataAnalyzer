from unicodedata import name
import numpy as np
import tkinter as tk
from tkinter import filedialog
import os
from csv import reader
import csv
from src.DiagnosticData import DiagnosticaData
from enum import IntEnum
import sys
import re
import time
from collections import OrderedDict
from datetime import datetime

#set DEBUG_TRACE equal to True for Enabling the Traces
#debug activity
DEBUG_TRACE = False
# global variable
alarm_list    = []
activity_list = []
timeReference = 0
entry_time=0
def Convert24(time):
    # Parse the time string into a datetime object
    t = datetime.strptime(time, "%I:%M:%S:%f %p")
    # Format the datetime object into a 24-hour time string
    t = t.strftime('%H:%M:%S:%f')
    #return a list of [h,m,s,ms]
    t = str(t).split(":")
    return t

def progress_bar(progress,total):
    percent= 100 * progress/total
    bar = "*"*int(percent) + "_"*int(100-percent)
    if int(percent)%10 and percent != 100:
        print("\r{} {}/100".format(bar,int(percent)), end="") 
    elif percent==100:
        print("\r{} 100/100".format(bar), end="")


def extract_activity(row):
    activity="activities:"
    end_activity = "}"
    start_index = row.index(activity)
    stop__index = row.index(end_activity)
    activity_name = row[start_index+len(activity):stop__index].strip()
    return activity_name

def extract_alarm(row):
    trigger= "Trigger: "
    origin = "Origin:"
    start_index = row.index(trigger)
    stop__index = row.index(origin)
    trigger_name = row[start_index+len(trigger):stop__index].strip()
    return trigger_name

def extract_time(row): 
    up_to_index = row.index("M,")
    start_from_index = row.index("T")+1
    row = row[start_from_index:up_to_index+1]
    list_of_time_value = Convert24(row)

    list_of_time_value[0] = int(list_of_time_value[0])
    list_of_time_value[1] = int(list_of_time_value[1])
    list_of_time_value[2] = int(list_of_time_value[2])
    list_of_time_value[3] = float(list_of_time_value[3])/1000000

    return list_of_time_value


def compute_delta_sec(list_h_min_sec_msec, ref):
    # initialyze variables
    global entry_time
    entry_time = str(ref[0])+":"+str(ref[1])+":"+str(ref[2])
    #print("entry_time",entry_time)
    delta_sec = 0
    hours = 0
    minute = 0
    seconds = 0
    # compute Hours
    hours = list_h_min_sec_msec[0] - ref[0]
    hours = hours* 60 *60    
    # compute Minutes
    minute = list_h_min_sec_msec[1] - ref[1]
    minute = minute* 60

    # compute Seconds
    seconds = list_h_min_sec_msec[2] - ref[2]

    #compute msec
    msec = list_h_min_sec_msec[3] - ref[3]

    delta_sec = hours + minute + seconds + msec
            
    return delta_sec

def extract_reading(text,key):
    return_value = 0
    return_value = text[text.index(key)+1]
    return return_value
              
def fill(text,Data):
    text = re.sub(r'\s+', ',', text)
    text = text.split(sep=',')
    text = [x.replace(":","") for x in text]
    for idx in Data:
        #the parameter is in the current row
        if idx[0] in text:
            value = extract_reading(text,idx[0])
            tmp = idx[1][1]
            if str(tmp.__name__ )!="Numeric":
                value = tmp[value].value 
            idx[1][0].append(float(value))
        # the parameters is not in the following row
        else:
            if not idx[1][0]:
                #if the list is empty add 0
                idx[1][0].append(float(0))
            else:
                #otherwise fill with the latest reading
                idx[1][0].append(idx[1][0][-1])

def SetTime(Data,row):
    time_tmp = extract_time(row)
    #print("Time: ", time_tmp)
    if not Data.Params[0][1][0]: 
        Data.Params[0][1][1] = time_tmp
    Data.Params[0][1][0].append(compute_delta_sec(time_tmp,Data.Params[0][1][1]))


def scrub_diagnostic(file_name):
    try:
        DataLogs = file_name
        name=file_name.replace('DiagnosticLog', 'Log')
        OutputName = name.replace('.txt', '_') + 'output_diagnostic.csv'

        print("File Selected: {}\n".format(DataLogs))
        print(" Data Extraction in Progress....\n")
        #time.sleep(1.0)

        myData = DiagnosticaData()

        lines_to_find = ["IND_BLOOD_CIRCUIT_STATUS","IND_DIALYSATE_CIRCUIT_STATUS","IND_TREATMENT_DATA","IND_BLOOD_CIRCUIT_PARAMETERS","IND_DIALYSATE_CIRCUIT_PARAMETERS"]

        alarm_to_plot = "IND_ALARM_CONDITION_ACTIVATION"

        activity_to_plot ="IND_HEMODIALYSIS_ACTIVITY"

        with open(DataLogs) as diagnosticFile:
                rows = diagnosticFile.readlines()
                #drop the last row because it could be interrupted by the Power OFF of the console 
                rows = rows[:-1]
                progress_bar(0,len(rows))
                counter=0
                for row in rows:
                    counter+=1
                    progress_bar(counter,len(rows))
                    if alarm_to_plot in row:
                        myData.Params[1][1][0].append(extract_alarm(row))
                        SetTime(myData,row)
                        fill(row,myData.Params[2:])
                    elif activity_to_plot in row:
                        myData.Params[1][1][0].append(extract_activity(row))
                        SetTime(myData,row)
                        fill(row,myData.Params[2:])
                    for elm in lines_to_find:
                        if elm in row:
                            SetTime(myData,row)
                            myData.Params[1][1][0].append("None") 
                            fill(row,myData.Params[2:])
                            break
                            
                            
                    
        progress_bar(len(rows),len(rows))
        if DEBUG_TRACE:
            print("***Events**** \n")
            for x in myData.Params:
                print("{}\n".format(x))


    ####### Generate CSV file section ##########
        print("\n Generating CSV file as Output... \n")
        progress_bar(0,len(rows))
        row=0
        with open(OutputName, 'w') as f:
            for elm in myData.Params:
                f.write('%s,' % elm[0])
            f.write('\n')
            while(row < len(myData.Params[0][1][0])):
                progress_bar(row,len(myData.Params[0][1][0]))
                for elm in myData.Params:
                    if elm[0] == 'Event':
                        if elm[1][0][row]=='None':
                            f.write(',')
                        else:
                            string=str(elm[1][0][row])
                            f.write(string+",")
                    else:
                        f.write('%f,' % elm[1][0][row])
                f.write("\n")
                row+=1
        progress_bar(len(myData.Params[0][1][0]),len(myData.Params[0][1][0]))
        print("\nScript Completed !!!")
        return OutputName, entry_time
    except:
        print("Error: File not correct")
        if os.path.isfile(OutputName):    
            os.remove(OutputName)
        return False, ''

