import os
import pickle
import time
import localFileMan


class changeRunner:

    # Given the list of files to upload/download/delete for client & services,
    # execute all changes.
    # NB services will only need upload/delete calls, as downloads are done.

    fileMan = None
    DROPIGNORE = 'dropIgnore.pickle'
    DRIVEIGNORE = 'driveIgnore.pickle'

    def __init__(self):
        changeRunner.fileMan = localFileMan.fileMan()

    def runClientUpdates(self):
        oldID = changeRunner.fileMan.getIndexID()
        print '----------------------------------------'
        while not oldID < changeRunner.fileMan.getIndexID():
            print 'Waiting for client update...'
            time.sleep(3)
        print '----------------------------------------'
        print 'Client Updates Finished'
        changeRunner.fileMan.clearToDo()

    def bulkServiceUpdate(self, uploadDict, dropRealIndex, driveRealIndex):
        # Given a dict of files to upload to services, determine
        # split into two dicts (one for each service) then runServiceUpdates
        dropDict = {}
        driveDict = {}
        for lowPath, meta in uploadDict.iteritems():
            destination = meta[3]
            if destination == 'dropbox':
                dropDict[lowPath] = meta
            elif destination == 'drive':
                driveDict[lowPath] = meta
            elif destination == 'dropdrive':
                dropDict[lowPath] = meta
                driveDict[lowPath] = meta
            else:
                print '----------------------------------------'
                print 'Destination error in bulkServiceUpdate()'
        # Build ignore lists for next delta call, gets cleared @ end of delta()
        self.buildIgnoreLists(dropDict, 'dropbox')
        self.buildIgnoreLists(driveDict, 'drive')
        # Update Dropbox
        self.runServiceUpdates(dropDict, dropRealIndex)
        # Update Drive
        self.runServiceUpdates(driveDict, driveRealIndex)

    def runServiceUpdates(self, uploadDict, serviceRealIndex):
        if uploadDict is not None:
            for lowPath, meta in uploadDict.iteritems():
                modTime = meta[0]
                upperRelPath = meta[1]
                # Check file exists
                basePath = '/home/cianb/CloudDown/'
                fullPath = os.path.join(basePath, upperRelPath)
                serviceRealIndex.add(upperRelPath, modTime, sourceRemote=True)

    def runServiceDeletes(self, deleteDict, serviceFileMen):
        # Given a list of files to delete, and list of file managers,
        # delete from appropriate services.
        dropFileMan = serviceFileMen[0]
        driveFileMan = serviceFileMen[1]
        for lowPath, meta in deleteDict.iteritems():
            destination = meta[3]
            if destination == 'dropbox':
                dropFileMan.deleteRemote(lowPath)
            elif destination == 'drive':
                driveFileMan.deleteRemote(lowPath)
            elif destination == 'dropdrive':
                dropFileMan.deleteRemote(lowPath)
                driveFileMan.deleteRemote(lowPath)
            else:
                print '----------------------------------------'
                print 'Destination error in runServiceDeletes()'

    def buildIgnoreLists(self, uploadDict, serviceName):
        ignoreList = []
        for lowPath, meta in uploadDict.iteritems():
            ignoreList.append(lowPath)
        if serviceName == 'dropbox':
            with open(changeRunner.DROPIGNORE, 'wb') as drop_ignore:
                pickle.dump(ignoreList, drop_ignore)
        elif serviceName == 'drive':
            with open(changeRunner.DRIVEIGNORE, 'wb') as drive_ignore:
                pickle.dump(ignoreList, drive_ignore)
        elif serviceName == 'dropdrive':
            with open(changeRunner.DROPIGNORE, 'wb') as drop_ignore:
                pickle.dump(ignoreList, drop_ignore)
            with open(changeRunner.DRIVEIGNORE, 'wb') as drive_ignore:
                pickle.dump(ignoreList, drive_ignore)
        else:
            print '----------------------------------------'
            print 'serviceName error in buildIgnoreLists()'
