import json

from pytz import timezone, all_timezones, common_timezones, country_timezones
import pathlib
from Settings import GetIsDebugMode, GetFilePathSeperator

DebugMode = GetIsDebugMode()
FILE_PATH_SEPERATOR = GetFilePathSeperator()

pathToFile = str(pathlib.Path(__file__).parent.resolve()) + FILE_PATH_SEPERATOR + "TimeZoneDictionary.txt"

timeZoneDictionary = {}

# helper functions for this module

def FillTimeZoneDictionary():
    with open(pathToFile) as f:
        data = f.read()

    global timeZoneDictionary
    timeZoneDictionary = json.loads(data)

def SaveDictionaryToFile():
    with open(pathToFile, "w") as textFile:
        textFile.write(json.dumps(timeZoneDictionary))

def GetTimeZoneFromString(timeZoneStr : str):
    
    if timeZoneStr in country_timezones:
        return timezone(country_timezones(timeZoneStr)[0])
    
    if timeZoneStr in common_timezones or timeZoneStr in all_timezones:
        return timezone(timeZoneStr)
    
    for timeZone in common_timezones:
        if timeZoneStr in timeZone:
            return timezone(timeZone)

    return

# functions for outside of this module

def SetUserTimeZone(id : int, usertimezone):

    timezoneObject = GetTimeZoneFromString(usertimezone)

    if not timezoneObject:
        return False

    FillTimeZoneDictionary()

    timeZoneDictionary[str(id)] = str(timezoneObject)

    if DebugMode:
        print(timeZoneDictionary)

    SaveDictionaryToFile()

    return True


def GetUserTimeZone(id : int):

    FillTimeZoneDictionary()

    if str(id) in timeZoneDictionary:
        return timezone(timeZoneDictionary[str(id)])

    if DebugMode:
        print("No time zone found for user " + str(id))

def GetAllUsersAndTimeZones():
    return timeZoneDictionary