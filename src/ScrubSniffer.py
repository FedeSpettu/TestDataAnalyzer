import os
import tkinter as tk
from tkinter import filedialog
import json
from datetime import datetime
from collections import OrderedDict

##### Config parameters #####
ELEM_TO_PLOT_AS_DATA =[
    'BloodCircuitStatusIndication',
    'BloodCircuitParameters',
    'BloodCircuitPrimeAndFlushAccumulatedVolumeIndication',
    'DialysateCircuitStatusIndication',
    'DialysateCircuitParameters',
    'TreatmentDataIndication',
    'AdjustChlorideAndBicarbonateAccumulatedVolumeIndication',
]

DATA_KEYS_TO_FILTER =[
    'RGBData',
]

EVENT_KEYS_TO_FILTER = [
    'DialysateAdditionalDataIndication', #Not used in the current version
    'BloodAdditionalDataIndication', #Not used in the current version
]

EVENT_VALUES_TO_FILTER =[
    'REQ_CHECK_IN',
    'RESP_CHECK_IN',
]

VALVE_ENUM =[
    'VALVE_FAILURE',
    'VALVE_DEACTIVATED',
    'VALVE_ACTIVATED',
    'VALVE_OVERCURRENT',
    'VALVE_OPEN_LOAD',
    'VALVE_DRIVER_OVERTEMPERATURE',
    'VALVE_NOT_CONNECTED',
    'VALVE_NO_CHANGE',
]

PUMP_ENUM=[
    'PUMP_FAULTED',
    'PUMP_DEACTIVATED',
    'PUMP_ACTIVATED',
]

PREDEFINED_ENUMS = {
    #VALVES
    'DialysateCircuitStatusIndication_ValveStatus_FastFillValveState':VALVE_ENUM,
    'DialysateCircuitStatusIndication_ValveStatus_SodiumDiverterValve3State':VALVE_ENUM,
    'DialysateCircuitStatusIndication_ValveStatus_MicrobialFilterValveState':VALVE_ENUM,
    'DialysateCircuitStatusIndication_ValveStatus_DrainDiverterValveState':VALVE_ENUM,
    'DialysateCircuitStatusIndication_ValveStatus_DialysateBypassValveState':VALVE_ENUM,
    'DialysateCircuitStatusIndication_ValveStatus_SodiumDiverterValve1State':VALVE_ENUM,
    'DialysateCircuitStatusIndication_ValveStatus_SorbentIsolationValveState':VALVE_ENUM,
    'DialysateCircuitStatusIndication_ValveStatus_SterilantRinseValve1State':VALVE_ENUM,
    'DialysateCircuitStatusIndication_ValveStatus_SterilantRinseValve2State':VALVE_ENUM,
    'DialysateCircuitStatusIndication_ValveStatus_BleachRinseValveState':VALVE_ENUM,
    'DialysateCircuitStatusIndication_ValveStatus_SorbentBypassValveState':VALVE_ENUM,
    'DialysateCircuitStatusIndication_ValveStatus_SodiumDiverterValve2State':VALVE_ENUM,
    'DialysateCircuitStatusIndication_ValveStatus_UltrafiltrationPumpRecirculationValveState':VALVE_ENUM,
    'DialysateCircuitStatusIndication_ValveStatus_IsolationValveState':VALVE_ENUM,
    'DialysateCircuitStatusIndication_ValveStatus_VentValve3State':VALVE_ENUM,
    'DialysateCircuitStatusIndication_ValveStatus_VentValve1State':VALVE_ENUM,
    'DialysateCircuitStatusIndication_ValveStatus_WaterPumpRecirculationValveState':VALVE_ENUM,
    'DialysateCircuitStatusIndication_ValveStatus_BleachUpdateValveState':VALVE_ENUM,
    'DialysateCircuitStatusIndication_ValveStatus_BicarbonateDiverterValveState':VALVE_ENUM,
    'DialysateCircuitStatusIndication_ValveStatus_VentValve2State':VALVE_ENUM,
    'DialysateCircuitStatusIndication_ValveStatus_BleachRecirculationValveStatus':VALVE_ENUM,
    'BloodCircuitStatusIndication_BloodLineValveStatus_VenousDripValveStatus':VALVE_ENUM,
    'BloodCircuitStatusIndication_BloodLineValveStatus_ArterialDripValveStatus':VALVE_ENUM,
    'BloodCircuitStatusIndication_BloodLineValveStatus_PumpPositiveValveStatus':VALVE_ENUM,
    'BloodCircuitStatusIndication_BloodLineValveStatus_PumpNegativeValveStatus':VALVE_ENUM,
    'BloodCircuitStatusIndication_VenousLineClampStatus_VenousLineClampValve':VALVE_ENUM,
    #PUMPS
    'DialysateCircuitStatusIndication_PumpStatus_BicarbonatePumpStatus':PUMP_ENUM,
    'DialysateCircuitStatusIndication_PumpStatus_DialysatePump2Status':PUMP_ENUM,
    'DialysateCircuitStatusIndication_PumpStatus_DialysatePump1Status':PUMP_ENUM,
    'DialysateCircuitStatusIndication_PumpStatus_InfusatePumpStatus':PUMP_ENUM,
    'DialysateCircuitStatusIndication_PumpStatus_WaterPumpStatus':PUMP_ENUM,
    'DialysateCircuitStatusIndication_PumpStatus_UltrafiltrationPumpStatus':PUMP_ENUM,
    'DialysateCircuitStatusIndication_PumpStatus_VacuumGearPumpStatus':PUMP_ENUM,
    'DialysateCircuitStatusIndication_PumpStatus_GasRemovalPumpStatus':PUMP_ENUM,
}

PREFILLED_COLUMN =[
    ('TimeSniffer','0'),
    ('Event',''),
]

PROTO_MESSAGE_GETTER = {
    'REQUEST':'TherapyRequest',
    'RESPONSE':'TherapyResponse',
    'INDICATION':'TherapyIndication',
    'CONFIRMATION':'TherapyConfirmation',
}

##### Working Variable #####
dataList = []
enumList = PREDEFINED_ENUMS
dataToPlot = OrderedDict(PREFILLED_COLUMN)

class Data:
    def __init__(self, time, name, value):
        self.time = time
        self.name = name
        self.value = value

##### functions #####
def ExtractData(time, name, dicData):
    for key in dicData.keys():
        if key in DATA_KEYS_TO_FILTER:
            continue
        stringName = name + '_'+ key
        if type(dicData[key]) is dict:
            ExtractData(time, stringName, dicData[key])
            continue
        elif type(dicData[key]) is int or type(dicData[key]) is float:
            value = str(dicData[key])
        elif type(dicData[key]) is str or type(dicData[key]) is list:
            value = GetEnum(stringName, str(dicData[key]))
        else:
            print('!!!! ERROR !!!! Unhandled Data type' + str(type(dicData[key])) +' for value '+ str(dicData[key]))
            exit(1)
        dataList.append(Data(time,stringName,value))
        if stringName not in dataToPlot:
            dataToPlot[stringName] = '0'

def GetStingFromEvent(initialString, dicEvent):
    if type(dicEvent) is str:
        string = initialString + '{' + dicEvent
    else:
        string = initialString + '{'
        for key in dicEvent.keys():
            if type(dicEvent[key]) is dict:
                string = GetStingFromEvent(string + key + ':', dicEvent[key]) + '}'
            elif type(dicEvent[key]) is int or type(dicEvent[key]) is float:
                string = string + key + ':'+ str(dicEvent[key]) + '_'
            elif type(dicEvent[key]) is list:
                string = string + key + ':'+  str(dicEvent[key]).replace(',','_') + '_'
            elif type(dicEvent[key]) is str:
                string = string + key + ':'+ dicEvent[key] + '_'
            else:
                print('!!!! ERROR !!!! Unhandled Event type' + str(type(dicEvent[key])) +' for value '+ str(dicEvent[key]))
                exit(1)
    return string +'}'

def ExtractEvent(time, initialString, dicEvent = ''):
    if dicEvent != '':
        string = GetStingFromEvent(initialString,dicEvent)
    else:
        string = initialString
    dataList.append(Data(time,'Event',string))

timeReference = 0
def Getmsec(time):
    global timeReference
    dateTime = time[:-6].replace('T',' ').split('.')
    dateTimeFormatted = dateTime[0]+'.'+dateTime[1][:6] if len(dateTime) == 2 else dateTime[0]+'.000000'
    objTime = datetime.strptime(dateTimeFormatted, '%Y-%m-%d %H:%M:%S.%f')
    if timeReference == 0:
        timeReference = objTime.timestamp()
    deltaTime = round(objTime.timestamp() - timeReference, 6)
    return str(deltaTime)

def GetEnum(key, value):
    if key not in enumList:
        enumList[key] = []
    if value not in enumList[key]:
        enumList[key].append(value)
    return str(enumList[key].index(value))

##### main #####
def scrub_json(file_name):
    try:
        print('Getting json file...')
        
        jsonDataLogs = file_name

        jsonList=[]

        #Read json file
        print('\nReading json file...')
        with open(jsonDataLogs) as json_file:
            for jsonObj in json_file:
                if(jsonObj.startswith('[')):
                    continue
                if(jsonObj == ']\n'):
                    continue
                jsonObj = jsonObj.replace('},\n', '}\n')
                jsonDict = json.loads(jsonObj)
                jsonList.append(jsonDict)
            
        #Scan json list
        for js in jsonList:
            message =js['MESSAGE'][PROTO_MESSAGE_GETTER[js['MESSAGE']['ID']]]
            for key in message.keys():
                if key == 'ID' and len(message.keys()) > 1:
                    continue
                msec = Getmsec(js['TAG'])
                if key in ELEM_TO_PLOT_AS_DATA:
                    ExtractData(msec, key, message[key])
                elif key not in EVENT_KEYS_TO_FILTER and  message[key] not in EVENT_VALUES_TO_FILTER:
                    if (key == 'ID'):
                        ExtractEvent(msec, message[key])
                    else:
                        ExtractEvent(msec, message['ID']+':'+key, message[key])

        #Create CSV
        csvDataLogs = file_name.replace('.json', '_') + 'output_json.csv'
        print('\nWriting '+ csvDataLogs + ' file...')
        with open(csvDataLogs, 'w') as file:
            #Write columns name
            file.write(','.join(key for key in dataToPlot.keys()))
            file.write('\n')

            for data in dataList:
                if dataToPlot['TimeSniffer'] != data.time:
                    #Print dataToPlot to new line
                    file.write(','.join(value for value in dataToPlot.values()))
                    file.write('\n')
                    dataToPlot['TimeSniffer'] = data.time

                #Update data to plot
                dataToPlot[data.name] = data.value

                if data.name == 'Event':
                    #Print dataTEvent to new line
                    file.write(','.join(value for value in dataToPlot.values()))
                    file.write('\n')
                    dataToPlot['Event'] =''

            #Create Enum CSV
            csvEnumsDataLogs = jsonDataLogs.replace('.json', '_ENUMS.csv')
            print('\nWriting '+ csvEnumsDataLogs + ' file...')
            with open(csvEnumsDataLogs, 'w') as file:
                file.write('Data Name,Enums\n')
                for key,valuesList in enumList.items():
                    file.write(key+',')
                    for value in valuesList:
                        file.write(value+':'+str(valuesList.index(value))+',')
                    file.write('\n')
            
            #Complete
            print('\nProcedure successfully completed!')
            return csvDataLogs
    except:
        print('Error: file not correctly formatted')
        try:
            if os.path.isfile(csvDataLogs):
                os.remove(csvDataLogs)
        except:
            # csvDataLogs was never defined, so just pass
            pass
        return False