import dropIndex as dropIndex
import dropRemoteCheck as dropRemoteCheck
import dropFileMan


class dropDriver:

    remoteCheck = None
    dropboxIndex = None
    fileMan = None

    def __init__(self, dropboxDirectory):

        dropDriver.fileMan = dropFileMan.dropFileMan(dropboxDirectory)
        # Create Dropbox index
        dropDriver.dropboxIndex = dropIndex.dropIndex(dropboxDirectory)
        # Do checks
        dropDriver.remoteCheck = dropRemoteCheck.dropRC(dropDriver.dropboxIndex)

    def checkRemote(self):
        # Remote Check
        dropDriver.remoteCheck.check(dropDriver.dropboxIndex)

    def getRealIndex(self):
        return dropDriver.dropboxIndex

    def printIndex(self):
        dropDriver.dropboxIndex.printIndex()

    def getFileMan(self):
        return dropDriver.fileMan
