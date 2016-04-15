import localFileMan
import execChanges
import time


class cSync:

    # First gets client index and compares to service indexes
    # Future calls compare new client index to old one to determine
    # what to upload/delete. Always returns a list of uploads/deletes
    # for each service

    fileMan = None
    PASTINDEX = 'pastIndex.pickle'
    pastIndex = {}
    CLIENTTODO = 'clientToDo.pickle'
    CHANGELISTID = 'changeListID.pickle'
    changeListID = None
    changer = None

    def __init__(self, dropRealIndex, driveRealIndex):
        # Get client index, compare to service ones,
        # build update lists, save as old index
        cSync.fileMan = localFileMan.fileMan()
        cSync.changer = execChanges.changeRunner()
        # Clear to-do to start
        cSync.fileMan.clearToDo()
        # Load the local index
        theIndex = cSync.fileMan.loadIndex()
        # Save index id as used, to detect update
        indexID = cSync.fileMan.getIndexID()
        cSync.fileMan.saveUsedID(indexID)
        # Split into Dropbox and Drive lists
        splitList = cSync.fileMan.indexSplit(theIndex)
        localDropIndex = splitList[0]
        localDriveIndex = splitList[1]
        # Compare indexes
        dropToDos = self.initProcessIndexes(localDropIndex,
                                            dropRealIndex.getIndex(),
                                            'dropbox')
        driveToDos = self.initProcessIndexes(localDriveIndex,
                                             driveRealIndex.getIndex(),
                                             'drive')
        # Allow client to update files then get dropbox & drive upload lists
        serviceUploadDicts = self.initClientUpdate(dropToDos, driveToDos)
        dropboxUploadDict = serviceUploadDicts[0]
        driveUploadDict = serviceUploadDicts[1]
        # Build ignore lists
        cSync.changer.buildIgnoreLists(dropboxUploadDict, 'dropbox')
        cSync.changer.buildIgnoreLists(driveUploadDict, 'drive')
        # Add to Dropbox
        cSync.changer.runServiceUpdates(dropboxUploadDict, dropRealIndex)
        # Add to Drive
        cSync.changer.runServiceUpdates(driveUploadDict, driveRealIndex)
        # Save index as used
        cSync.fileMan.saveUsedIndex(theIndex)
        print '----------------------------------------'
        print '---- Finished Inital Sync ----'

    def delta(self):
        # Checks for updates on client.
        # Returns
        # [{serviceUploads}, [serviceDeletes]]
        # Load used client index
        print '----------------------------------------'
        print '--- Checking Client (Delta) ---'
        oldIndex = cSync.fileMan.getUsedIndex()
        # Wait for new index
        oldID = cSync.fileMan.getIndexID()
        while not oldID < cSync.fileMan.getIndexID():
            print 'Waiting New Index...'
            time.sleep(3)
        # Get new client index
        newIndex = cSync.fileMan.loadIndex()
        # Compare these two indexes to determine Uploads & Deletes
        toUpload = []
        toServiceUpload = {}
        toServiceDelete = {}
        # Look for what to upload
        for newLow, newMeta in newIndex.iteritems():
            found = False
            for oldLow, oldMeta in oldIndex.iteritems():
                if newLow == oldLow:
                    found = True
                    oldMod = oldMeta[0]
                    newMod = newMeta[0]
                    if newMod > oldMod:
                        toUpload.append(newLow)
                        toServiceUpload[newLow] = newMeta
            if found is False:
                toUpload.append(newLow)
                toServiceUpload[newLow] = newMeta
        # Look for what to delete
        for oldLow, oldMeta in oldIndex.iteritems():
            found = False
            for newLow, newMeta in newIndex.iteritems():
                if oldLow == newLow:
                    found = True
            if found is False:
                toServiceDelete[oldLow] = oldMeta
        # Save client upload list
        cSync.fileMan.addToDoUploads(toUpload)
        # Return the upload/delete dict/list
        upDel = [toServiceUpload, toServiceDelete]
        # Save new index as old index
        cSync.fileMan.saveUsedIndex(newIndex)
        return upDel

    def initProcessIndexes(self, localServiceIndex, remoteServiceIndex, serviceName):
        # Compare the client files for a service and the services files
        # Returns a list with [serviceUpload, clientUpload, clientDownload]
        # serviceUpload is a dictionary
        # 'serviceName' should be 'dropbox' or 'drive'
        serviceUpload = {}
        clientDownload = {}  # of type {casePath = serviceName}
        clientUpload = []
        # Compare 'UP' - files compare local to remote
        print '----------------------------------------'
        print '----- Comparing client to remote ------'
        for localLowPath, localMeta in localServiceIndex.iteritems():
            found = False
            for remoteLowPath, remoteMeta in remoteServiceIndex.iteritems():
                if localLowPath == remoteLowPath:
                    # Found remote version, comapre mod times
                    found = True
                    localMod = localMeta[0]
                    remoteMod = remoteMeta[0]
                    if localMod > remoteMod:
                        # Local newer
                        serviceUpload[localLowPath] = localMeta
                        clientUpload.append(localLowPath)
                        print '----------------------------------------'
                        print 'Added ' + str(localLowPath) + ' to upload list'
                    elif remoteMod > localMod:
                        # Remote newer
                        modTime = localMeta[0]
                        upperPath = localMeta[1]
                        clientDownload[upperPath] = serviceName
                        print '----------------------------------------'
                        print 'Added ' + str(localLowPath) + ' to download list'
                    else:
                        # Same, do nothing
                        print '----------------------------------------'
                        print 'Local & Remote Versions Same'
            if found is False:
                # Not on service
                serviceUpload[localLowPath] = localMeta
                clientUpload.append(localLowPath)
                print '----------------------------------------'
                print 'Added ' + str(localLowPath) + ' to upload list'
        # Compare 'DOWN' - remote files to local
        print '----------------------------------------'
        print '----- Comparing remote to local -----'
        for remoteLowPath, remoteMeta in remoteServiceIndex.iteritems():
            found = False
            for localLowPath, localMeta in localServiceIndex.iteritems():
                if localLowPath == remoteLowPath:
                    found = True
            if found is False:
                # File not found locally, add to client download list
                modTime = remoteMeta[0]
                upperPath = remoteMeta[1]
                clientDownload[upperPath] = serviceName
                print '----------------------------------------'
                print 'Added ' + str(upperPath) + ' to client download list'
        finishedList = [serviceUpload, clientUpload, clientDownload]
        return finishedList

    def initClientUpdate(self, dropToDos, driveToDos):
        # Buid the totoal list of uploads and downloads the client needs to do
        # Save the list. Wait for client to do them. Clear to-do file.
        # Return [DropboxUploads, DriveUploads]
        dropboxUploads = dropToDos[0]
        driveUploads = driveToDos[0]
        clientTotalUps = dropToDos[1] + driveToDos[1]
        clientTotalDowns = dict(dropToDos[2].items() + driveToDos[2].items())
        # Total list of uploads and downloads for client, plus empty deletes
        clientTotalToDo = [clientTotalUps, clientTotalDowns, []]
        # Save to do list for client to get
        cSync.fileMan.saveToDo(clientTotalToDo)
        # Wait for changes
        oldID = cSync.fileMan.getUsedID()
        print '----------------------------------------'
        while not oldID < cSync.fileMan.getIndexID():
            print 'Waiting for client update...'
            time.sleep(3)
        # Index ID is now larger, save it as used and continue.
        # Uploads/downloads have happened
        cSync.fileMan.saveUsedID(cSync.fileMan.getIndexID())
        # Clear the to-do list
        cSync.fileMan.clearToDo()
        returnList = [dropboxUploads, driveUploads]
        return returnList
