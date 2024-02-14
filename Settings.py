DebuggingMode = True
LinuxMode = False
SoundboardActive = False

def GetIsDebugMode():
    return DebuggingMode

if LinuxMode:
    FILE_PATH_SEPERATOR = '/'
else:
    FILE_PATH_SEPERATOR = '\\'

def GetFilePathSeperator():
    return FILE_PATH_SEPERATOR

def GetIsSoundboardActive():
    return SoundboardActive