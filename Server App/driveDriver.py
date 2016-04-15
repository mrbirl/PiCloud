import driveAuth
import driveFileMan
import driveIndex as driveIndex
import driveRemoteCheck as driveRemote


class driveDriver:

    client = None
    driveIndex = None
    driveRemote = None
    Stop = False
    fileMan = None

    def __init__(self, directory):
        driveDriver.client = driveAuth.getClient()
        driveDriver.driveIndex = driveIndex.driveIndex(directory,
                                                       driveDriver.client)
        driveDriver.driveRemote = driveRemote.driveRC(driveDriver.driveIndex,
                                                      driveDriver.client)
        driveDriver.fileMan = driveFileMan.driveFileMan(directory,
                                                        driveDriver.client)

    def checkRemote(self):
        driveDriver.driveRemote.check(driveDriver.driveIndex)

    def getRealIndex(self):
        return driveDriver.driveIndex

    def getClient(self):
        return driveDriver.client

    def printIndex(self):
        print driveDriver.driveIndex.printIndex()

    def getFileMan(self):
        return driveDriver.fileMan
