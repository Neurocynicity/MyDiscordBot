import json

class FileDataAccessor:

    def __init__(self, FilePath : str) -> None:
        self.FilePath = FilePath

    def GetData(self):
        with open(self.FilePath) as f:
            data = f.read()

        return json.loads(data)
    
    def SetData(self, modifiedFile):
        with open(self.FilePath, "w") as textFile:
            textFile.write(json.dumps(modifiedFile))