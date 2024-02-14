import re

from datetime import datetime, timedelta, date
from Settings import GetIsDebugMode

import pytz

DebugMode = GetIsDebugMode()

def GetLocalTimeForTimeZone(timeZone):
    return datetime.now(timeZone).strftime("%B %d, %H:%M")

# this is the class that defines a way of writing out times
# using this we can quickly add or change existing ways to write the time
# see the list below for examples
class TimeFormat:
    def __init__(self, regex : str, formatString : str, timeIdentifier : str, getPostfixRegex=""):
        self.regex = regex
        self.formatString = formatString
        self.timeIdentifier = timeIdentifier
        self.getPostfixRegex = getPostfixRegex

# these are executed in order of this list
# to increase priority of an option, add it to the list earlier
possibleTimeFormats = []
possibleTimeFormats.append(TimeFormat("\d+:\d+\s*[apAP][mM]", "%H:%M", "t", "\d+:\d+"))
possibleTimeFormats.append(TimeFormat("\d+:\d+", "%H:%M", "t"))
possibleTimeFormats.append(TimeFormat("\d+\s*[apAP][mM]", "%H", "t", "\d+"))
possibleTimeFormats.append(TimeFormat("\d+h\d+", "%Hh%M", "t", "\d+h\d+"))
possibleTimeFormats.append(TimeFormat("\d+h", "%Hh", "t", "\d+h"))

def ReplaceTimesInStringWithTimeStamps(inputString : str, userTimeZone):

    matches = GetTimesInMessage(inputString, userTimeZone)

    for match in matches:
        
        timestamp = int(match[1].timestamp())
        formattedTimeString = "<t:" + str(timestamp) + ":" + match[2].timeIdentifier + ">"
        inputString = re.sub(match[0], formattedTimeString, inputString, 1) 
    
    return inputString

# finds all times and returns a list of tuples
# first is the string matched, 2nd is the time object created from it
# 3rd is the found format object
def GetTimesInMessage(inputTime : str, userTimeZone):
    
    if userTimeZone == None:
        print("User has no time zone role, UTC will be used")
        userTimeZone = pytz.utc

    matches = []

    for times in possibleTimeFormats:

        results = re.findall(times.regex, inputTime)
        
        for result in results:
            finalResult = (result, GetLocalTimeOfTimeString(result, times, userTimeZone), times)

            if finalResult[1] != None:
                matches.append(finalResult)
        
    return matches

def GetLocalTimeOfTimeString(timeString : str, timeFormat, userTimeZone):
    
    formatString = timeFormat.formatString
    
    if len(timeFormat.getPostfixRegex) > 0:
        formatString = formatString + re.sub(timeFormat.getPostfixRegex, "", timeString)

    # try parsing it as a time, if it can't be parsed as a time then it's probably
    # not an actual time and being noticed incorrectly
    try:
        timeObject = datetime.strptime(timeString, formatString)

    except:

        if DebugMode:
            print(timeString + " discarded as it's not a valid time")

        return None

    # am/ pm isn't supported in the function i'm using to generate
    # times and timestamps, so we add 12 hours here if we find pm
    # and if it isn't 12 a/pm.  Those are handled seperately below
    isPmTime = re.search("pm", timeString.lower()) is not None
    isAmTime = re.search("am", timeString.lower()) is not None

    hasAmPm = isAmTime or isPmTime

    if timeObject.hour < 12 and isPmTime:

        # print("pm time found! adding 12 hours")
        timeObject += timedelta(hours=12)

    # this makes 12am 00:00 and leaves 12pm as 12:00
    elif timeObject.hour == 12 and not isPmTime and hasAmPm:
        timeObject -= timedelta(hours=12)

    if DebugMode:
        print(timeString + " => " + str(timeObject))

    # here we want to set the date to today
    # CHANGE THIS IF USERS CAN ENTER DATES TOO

    if DebugMode:
        print(str(timeObject.date()) + " == " + str(date(1900, 1, 1)))

    if timeObject.date() < date(1900, 1, 5):
        
        currentDate = datetime.now(userTimeZone).date()
        timeObject = timeObject.replace(year=currentDate.year, month=currentDate.month, day=currentDate.day)

    # make it the user's time zone
    timeObject = userTimeZone.localize(timeObject)

    if DebugMode:
        print("in user's local time zone the translated time is " + str(timeObject))

    # now we convert it from my time to the user's local time
    # timeObject = timeObject.astimezone(userTimeZone)
    # if time.daylight > 0:
    #     timeObject += timedelta(hours=1)

    return timeObject

# print(ReplaceTimesInStringWithTimeStamps("||14:00||", pytz.timezone("CET")))
# print(ReplaceTimesInStringWithTimeStamps("It's 12 pm and 12:00 midday and 12am 00:00 morning, 4:30 pm 4 am 4 pm 16:00 am 16:00 pm", pytz.timezone("CET")))