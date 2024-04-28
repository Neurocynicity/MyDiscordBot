import pathlib
from FileDataAccessorModule import FileDataAccessor
from Settings import GetFilePathSeperator

FILE_PATH_SEPERATOR = GetFilePathSeperator()

pathToFile = str(pathlib.Path(__file__).parent.resolve()) + FILE_PATH_SEPERATOR + "FriendCodes.txt"
dataAccessor = FileDataAccessor(pathToFile)
currentData : dict = dataAccessor.GetData()

def SetFriendCodeOfUser(user_id : int, friendCode : str):
    currentData[str(user_id)] = friendCode
    dataAccessor.SetData(currentData)

def GetFriendCodeOfUser(user_id : int):

    if str(user_id) in currentData.keys():
        return currentData[str(user_id)]
    
    return None

def RemoveUserFriendCode(user_id : int):
    
    if str(user_id) in currentData.keys():
        del currentData[str(user_id)]
        dataAccessor.SetData(currentData)
        return True
    
    return False