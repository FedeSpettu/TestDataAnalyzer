from enum import IntEnum
from collections import OrderedDict

class Numeric:
    pass

class DoorStatus(IntEnum):
    DOOR_CLOSED = 0,
    DOOR_OPEN = 1

class OverCurrentSensorStatus(IntEnum):
    OC_SENSOR_NORMAL = 0,
    OC_SENSOR_OVERCURRENT = 1

class ClampSensorStatus(IntEnum):
    CLAMP_OPEN = 0,
    CLAMP_RECHARGE = 1,
    CLAMP_BETWEEN_RECHARGE_AND_CLOSED_ON_LINE = 2,
    CLAMP_CLOSED_ON_LINE = 3,
    CLAMP_BETWEEN_CLOSED_AND_CLOSED_ON_LINE = 4,
    CLAMP_CLOSED = 5,
    CLAMP_UNCALIBRATED = 6

class LineClampPumpStatus(IntEnum):
    PUMP_OFF = 1,
    PUMP_ON = 2

class VenousAirSensorStatus(IntEnum):
    VENOUS_AIR_SENSOR_DETECTED_AIR = 1,
    VENOUS_AIR_SENSOR_DETECTED_NO_AIR = 2

class VenousBloodSensorStatus(IntEnum):
    VENOUS_BLOOD_SENSOR_NOT_CALIBRATED = 1,
    VENOUS_BLOOD_SENSOR_SALINE_IN_TUBING = 2,
    VENOUS_BLOOD_SENSOR_BLOOD_IN_TUBING = 3

class ValveStatus(IntEnum):
    VALVE_FAILURE = 0,
    VALVE_DEACTIVATED = 1,
    VALVE_ACTIVATED = 2,
    VALVE_OVERCURRENT = 3,
    VALVE_OPEN_LOAD = 4,
    VALVE_DRIVER_OVERTEMPERATURE = 5,
    VALVE_NOT_CONNECTED = 6,
    VALVE_NO_CHANGE = 7

class ConnectorStatus(IntEnum):
    CONNECTOR_NOT_CONNECTED = 0,
    CONNECTOR_CONNECTED = 1

class HeaterControlSensorStatus(IntEnum):
    HEATER_CNTL_SENSOR_ON = 1,
    HEATER_CNTL_SENSOR_OFF = 2,
    HEATER_CNTL_SENSOR_OVERTEMPERATURE = 3

class PumpStatus(IntEnum):
    PUMP_FAULTED = 0,
    PUMP_DEACTIVATED = 1,
    PUMP_ACTIVATED = 2

class ASPS_CapStatus(IntEnum):
    ASPSCAPSTATUS_OPEN = 1,
    ASPSCAPSTATUS_CLOSED = 2

class ASPS_CarrierDetected(IntEnum):
    YES = 1,
    NO = 2

class DialysatePathState(IntEnum): 
    DIALYSATE_PATH_STATE_DIALYSIS_FLOW = 1,
    DIALYSATE_PATH_STATE_DIALYSIS_BYPASS = 2,
    DIALYSATE_PATH_STATE_DIALYSIS_ISOLATE = 3,
    DIALYSATE_PATH_STATE_MICROBIAL_FILTER_FLUSH = 4,
    DIALYSATE_PATH_STATE_OTHER = 5

class BloodDetected(IntEnum):
    BLOOD_DETECTED = 1,
    BLOOD_NOTDETECTED = 2

class BloodPumpPosition(IntEnum):
    NONE = 1,
    NORTH = 2,
    SOUTH = 3,
    EAST = 4,
    WEST = 5


class DiagnosticaData:
    def __init__(self):
        # build dictionary to fill
        self.Params=[
        #Time
        ("RelTime",[[], 0]),
        #Event
        ("Event",[[], 0]),
        ("ArterialInletPressureSensor",[[],Numeric]),
        ("VenousPressureSensor",[[],Numeric]),
        ("PneumaticPressureSensor",[[],Numeric]),

        #BloodPumpStatus
        ("BloodPumpSpeed",[[],Numeric]),
        ("BloodPumpDoorSensor",[[],DoorStatus]),
        ("BloodPumpOvercurrentSensor",[[],OverCurrentSensorStatus]),

        #VenousLineClampStatus
        ("SensorStatus",[[],ClampSensorStatus]), 
        ("VenousLineClampValve",[[],ValveStatus]),
        ("LineClampPump",[[],LineClampPumpStatus]),

        #OtherBloodCircuitStatus
        ("HeparinPumpSensor",[[],Numeric]),
        ("VenousAirSensor",[[],VenousAirSensorStatus]),
        ("VABSColorVoltageValue",[[],Numeric]),
        ("UltrasonicVABSVoltage",[[],Numeric]),
        ("VenousBloodSensor",[[],VenousBloodSensorStatus]),

        #CabinetTemperatureStatus
        ("DUCP_CabinetTemperature",[[],Numeric]),
        ("DUPP_CabinetTemperature",[[],Numeric]),
        ("TBCP_CabinetTemperature",[[],Numeric]),
        ("TBPP_CabinetTemperature",[[],Numeric]),
        ("TSCP_CabinetTemperature",[[],Numeric]),
        ("TSPP_CabinetTemperature",[[],Numeric]),

        #BloodLineValveStatus
        ("VenousDripValveStatus",[[],ValveStatus]), 
        ("ArterialDripValveStatus",[[],ValveStatus]),
        ("PumpPositiveValveStatus",[[],ValveStatus]),
        ("PumpNegativeValveStatus",[[],ValveStatus]),
        
        #DialyzerBypassConnectorSensors
        ("DialyzerInConnectorStatus",[[],ConnectorStatus]),
        ("DialyzerOutConnectorStatus",[[],ConnectorStatus]),

        #ConductivitySensors
        ("FinalConductivitySensor",[[],Numeric]),
        ("Online_kTV_ConductivitySensor",[[],Numeric]),
        ("SorbentConductivitySensor",[[],Numeric]),
        ("PreSorbentConductivitySensor",[[],Numeric]),
        ("BicarbonateConductivitySensor",[[],Numeric]),
        ("TargetBicarbonateConductivitySensor",[[],Numeric]),
        ("TargetFinalConductivitySensor",[[],Numeric]),
        ("TargetPreSorbentConductivitySensor",[[],Numeric]),
        ("TargetSorbentConductivitySensor",[[],Numeric]),
        ("FinalConductivitySensorRawVoltage",[[],Numeric]),
        ("OnlinekTVConductivitySensorRawVoltage",[[],Numeric]),
        ("SorbentConductivitySensorRawVoltage",[[],Numeric]),
        ("BicarbonateConductivitySensorRawVoltage",[[],Numeric]),
        ("PreSorbentConductivitySensorRawVoltage",[[],Numeric]),

        #HeaterCntlSensorStatus
        ("HeaterCntlSensorStatus",[[],HeaterControlSensorStatus]),

        #TemperatureSensors
        ("FinalTemperatureSensor",[[],Numeric]),
        ("Online_kTV_TemperatureSensor",[[],Numeric]),
        ("SorbentTemperatureSensor",[[],Numeric]),
        ("HeaterInletTemperatureSensor",[[],Numeric]),
        ("DialysateTemperatureInletSensor",[[],Numeric]),
        ("HeaterOverTemperatureSensor",[[],Numeric]),
        ("PreSorbentTemperatureSensor",[[],Numeric]),
        ("BicarbonateTemperatureSensor",[[],Numeric]),
        ("ASPS_Temperature",[[],Numeric]),
        ("SorbentChamberTemperatureSensor",[[],Numeric]),

        #BloodLeakDetector
        ("BloodLeakDetector",[[],Numeric]),

        #FlowSensors
        ("OutletFlowSensorWithUF",[[],Numeric]),
        ("InletFlowSensor",[[],Numeric]),
        ("InletProtectiveSensor",[[],Numeric]),
        ("OutletFlowSensorWithUF2",[[],Numeric]),
        ("InflowVolume",[[],Numeric]),
        ("OutflowVolume",[[],Numeric]),

        #PressureSensors
        ("SorbentPressureSensor",[[],Numeric]),
        ("MicrobialFilterPressureSensor",[[],Numeric]),
        ("DialysatePressureInletSensor",[[],Numeric]),
        ("SorbentOutletPressureSensor",[[],Numeric]),
        ("DegasVesselPressureSensor",[[],Numeric]),
        ("FlowRateCompensatedSorbentInletPressure",[[],Numeric]),
        ("FlowRateCompensatedMicrobialFilterPressure",[[],Numeric]),
        ("MicrobialFilterPermeability",[[],Numeric]),
        ("BaselineMicrobialFilterPermeability",[[],Numeric]),
        ("AmbientPressureSensor",[[],Numeric]),
        ("BicarbonatePressureSensor",[[],Numeric]),
        ("OutletPressureSensor",[[],Numeric]),
        ("WaterPressureSensor",[[],Numeric]),

        #ValveStatus
        ("FastFillValveState",[[],ValveStatus]),
        ("SodiumDiverterValve3State",[[],ValveStatus]),
        ("MicrobialFilterValveState",[[],ValveStatus]),
        ("DrainDiverterValveState",[[],ValveStatus]),
        ("DialysateBypassValveState",[[],ValveStatus]),
        ("SodiumDiverterValve1State",[[],ValveStatus]),
        ("SorbentIsolationValveState",[[],ValveStatus]),
        ("SterilantRinseValve1State",[[],ValveStatus]),
        ("SterilantRinseValve2State",[[],ValveStatus]),
        ("BleachRinseValveState",[[],ValveStatus]),
        ("SorbentBypassValveState",[[],ValveStatus]),
        ("SodiumDiverterValve2State",[[],ValveStatus]),
        ("UltrafiltrationPumpRecirculationValveState",[[],ValveStatus]),
        ("IsolationValveState",[[],ValveStatus]),
        ("VentValve3State",[[],ValveStatus]),
        ("VentValve1State",[[],ValveStatus]),
        ("WaterPumpRecirculationValveState",[[],ValveStatus]),
        ("BleachUpdateValveState",[[],ValveStatus]),
        ("BicarbonateDiverterValveState",[[],ValveStatus]),
        ("VentValve2State",[[],ValveStatus]),
        ("BleachRecirculationValveStatus",[[],ValveStatus]),

        #PumpSetpoint
        ("WaterPumpSetpoint",[[],Numeric]),
        ("UltrafiltrationPumpSetpoint",[[],Numeric]),
        ("BicarbonatePumpSetpoint",[[],Numeric]),
        ("InfusatePumpSetpoint",[[],Numeric]),
        ("DialysatePump1Setpoint",[[],Numeric]),
        ("DialysatePump2Setpoint",[[],Numeric]),
        ("GasRemovalPumpSetpoint",[[],Numeric]),
        ("VacuumGearPumpSetpoint",[[],Numeric]),

        #PumpStatus
        ("DialysatePump1Speed",[[],Numeric]),
        ("VacuumGearPumpSpeed",[[],Numeric]),
        ("WaterPumpStatus",[[],PumpStatus]),
        ("UltrafiltrationPumpStatus",[[],PumpStatus]),
        ("BicarbonatePumpStatus",[[],PumpStatus]),
        ("InfusatePumpStatus",[[],PumpStatus]),
        ("DialysatePump1Status",[[],PumpStatus]),
        ("VacuumGearPumpStatus",[[],PumpStatus]),
        ("GasRemovalPumpStatus",[[],PumpStatus]),
        ("DialysatePump2Speed",[[],Numeric]),
        ("DialysatePump2Status",[[],PumpStatus]),


        #ChemicalSensors
        ("Dialysate_pH",[[],Numeric]),
        ("DialysateTotalAmmoniaConcentration",[[],Numeric]),
        ("ASPS_CapStatus",[[],ASPS_CapStatus]),
        ("ASPS_CarrierDetected",[[],ASPS_CarrierDetected]),
        ("AccumulatedAmmonia",[[],Numeric]),

        #DegasVesselLevelSensor
        ("DegasVesselLevelSensor",[[],Numeric]),

        #Parameters
        ("WaterLevel",[[],Numeric]),
        ("WasteLevel",[[],Numeric]),
        ("HeparinRate",[[],Numeric]),
        ("HeparinVolumeDelivered",[[],Numeric]),
        ("DialysateFlow",[[],Numeric]),
        ("DialysatePathState",[[],DialysatePathState]),
        ("TotalSorbentVolumeProcessed",[[],Numeric]),
        ("ElapsedTotalTime",[[],Numeric]),
        ("ElapsedTreatmentTime",[[],Numeric]),
        ("ElapsedSegmentTime",[[],Numeric]),
        ("TreatmentTimeRemaining",[[],Numeric]),
        ("BloodPumpFlowRate",[[],Numeric]),
        ("TotalBloodVolumeProcessed",[[],Numeric]),
        ("UFRate",[[],Numeric]),
        ("HDFluidRemoved",[[],Numeric]),
        ("IsolatedUFFluidRemoved",[[],Numeric]),
        ("ArterialInletStabilizedPressure",[[],Numeric]),
        ("ArterialHighLimit",[[],Numeric]),
        ("ArterialLowLimit",[[],Numeric]),
        ("VenousStabilizedPressure",[[],Numeric]),
        ("VenousHighLimit",[[],Numeric]),
        ("VenousLowLimit",[[],Numeric]),
        ("DialyzerTransmembranePressure",[[],Numeric]),
        ("DialysateTemperature",[[],Numeric]),
        ("DialysateConductivity",[[],Numeric]),
        ("RemainingUFTime",[[],Numeric]),
        ("ElapsedTreatmentDeliveryProfileTime",[[],Numeric]),
        ("ElapsedUFTime",[[],Numeric]),

        # Blood Circuit Parameters
        ("VenousAirBubbleSize",[[],Numeric]),
        ("VABS",[[],Numeric]),
        ("VABSCalibrationBaseline",[[],Numeric]),
        ("VLCSVoltage",[[],Numeric]),
        ("Detected",[[],BloodDetected]),
        ("Position",[[],BloodPumpPosition]),
        
        # Dialysate Circuit Parameters
        ("HeaterDutyCycle",[[],Numeric]),
        ("DVHPSetpoint",[[],Numeric]),
        ("DialysisTemperatureSetpoint",[[],Numeric]),
        ("MFPermeability",[[],Numeric])]