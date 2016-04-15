import time
import pickle
import localFileMan
import sftpManager


class cDriver:

    # Handles all interactions with the server

    sftpJob = None
    SERVERCLIST = 'serverChangeList.pickle'
    changeListID = 0
    theFileMan = None

    def __init__(self):

        cDriver.sftpJob = sftpManager.ftMan('theserver.com',
                                            'theuser',
                                            'thepassword')  # Connection deets
        cDriver.theFileMan = localFileMan.localFileMan()

    def run(self):
        updatesRan = self.runUpdates()
        print '----------------------------------------'
        print updatesRan

    def connect(self):
        # Start connection
        cDriver.sftpJob.connect()

    def close(self):
        # Close connection
        cDriver.sftpJob.close()

    def runUpdates(self):
        # Run any updates, return string to print on success
        # Get a change list
        changeList = self.getChangeList()
        print '----------------------------------------'
        print 'changeList:'
        print changeList
        # Upload any necessary files
        toUpload = changeList[0]
        cDriver.sftpJob.upload(toUpload)
        # Download any necessary files
        toDownload = changeList[1]  # These are upper case paths
        cDriver.sftpJob.download(toDownload)
        # Delete any necessary files
        toDelete = changeList[2]
        cDriver.theFileMan.deleteFiles(toDelete)
        # Upload Index
        cDriver.sftpJob.uploadIndex()
        successString = 'Updates ran ok, new index uploaded'
        # Change permissions of any created files/folders
        cDriver.theFileMan.changePathPermissions()
        return successString

    def getChangeList(self):
        # Download change list
        cDriver.sftpJob.downloadChangeList()
        try:
            with open(cDriver.SERVERCLIST, 'r') as change_list:
                theChangeList = pickle.load(change_list)
            return theChangeList
        except:
            print '----------------------------------------'
            print 'Couldnt find a change list, will wait and try again'
            time.sleep(2)
            return self.getChangeList()
