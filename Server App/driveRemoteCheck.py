import pickle
import driveFileMan
import localFileMan


class driveRC:

    # Check Drive for updates, update locally as needed

    client = None
    theDirectory = ''
    userName = None
    driveFileMan = None
    CURSOR = 'driveCursor.pickle'
    deltaCursor = None
    clientFileMan = None
    DRIVEIGNORE = 'driveIgnore.pickle'

    def __init__(self, driveIndex, theClient):
        driveRC.client = theClient
        driveRC.theDirectory = driveIndex.getDirectory()
        aboutStuff = driveRC.client.about().get().execute()
        driveFileMan.userName = aboutStuff['name']

        driveRC.driveFileMan = driveFileMan.driveFileMan(driveRC.theDirectory,
                                                         driveRC.client)
        driveRC.clientFileMan = localFileMan.fileMan()

        with open(driveRC.CURSOR, 'r') as the_cursor:
            driveRC.deltaCursor = pickle.load(the_cursor)

    def check(self, driveIndex):
        print '----------------------------------------'
        print '------ Checking Drive   ------'
        clientDownload = {}  # Dict of files for client to download
        clientDelete = []  # List of files for client to delete
        ignoreList = self.loadIgnoreList()
        deltaDict = driveRC.client.changes().list(includeDeleted=True,
                                                  startChangeId=driveRC.deltaCursor).execute()
        if not str(driveRC.deltaCursor) == str(deltaDict['largestChangeId']):
            # Cursor changed, change happened
            fileItems = deltaDict['items']
            for item in fileItems:
                isDeleted = item['deleted']
                if not isDeleted:
                    theFile = item['file']
                    fileID = theFile['id']
                    fileLabels = theFile['labels']
                    fileName = theFile['title']
                    isTrashed = fileLabels['trashed']
                    if isTrashed or isDeleted:
                        print '----------------------------------------'
                        print 'File "' + str(fileName) + '" was trashed'
                        # Add to client delete list
                        cDeletePath = driveRC.driveFileMan.pathBuilder(fileID)
                        cDeletePath = driveRC.driveFileMan.formatPath(cDeletePath)
                        lowerPath = cDeletePath.lower()
                        clientDelete.append(cDeletePath)
                        try:
                            driveIndex.delete(cDeletePath)
                            isDeleted = driveRC.driveFileMan.deleteLocal(driveIndex,
                                                                         fileID)
                            if isDeleted:
                                print '---------------------------------------'
                                print 'File deleted successfully!'
                        except:
                            print '----------------------------------------'
                            print 'File ' + str(fileName) + ' not deleted'
                    else:
                        # File to Download
                        modTime = item.get('modifiedDate')
                        if modTime is not None:
                            modTime = driveRC.driveFileMan.convertTime(modTime)
                            # Add here. If this file was added to dictionary
                            driveIndex.add(cDownloadPath,
                                           modTime,
                                           fileID=fileID)
                            # Earlier by execChanges, this will get the ID now,
                            # then won't download due to ignoreList
                            cDownloadPath = driveIndex.getPathById(fileID)
                            if cDownloadPath not in ignoreList:
                                print '---------------------------------------'
                                print 'File "' + str(fileName) + '" was added/updated'
                                fileDownloaded = driveRC.driveFileMan.downloadFile(fileID)
                                # Add to client download dict
                                clientDownload[cDownloadPath] = 'drive'
                            else:
                                driveIndex.delete(cDownloadPath)  # Remove from the index again
                else:
                    # Item deleted
                    deletedID = item['id']
                    # Add to client delete list
                    try:
                        cDeletePath = driveRC.driveFileMan.pathBuilder(fileID)
                        cDeletePath = driveRC.driveFileMan.formatPath(cDeletePath)
                        lowerPath = cDeletePath.lower()
                        clientDelete.append(cDeletePath)
                        driveIndex.delete(cDeletePath)
                        print '----------------------------------------'
                        print 'File was deleted'
                        isDeleted = driveRC.driveFileMan.deleteLocal(driveIndex, deletedID)
                        if isDeleted:
                            print '----------------------------------------'
                            print 'File deleted successfully!'
                    except:
                        print '----------------------------------------'
                        print 'Drive local file not deleted'
            driveRC.deltaCursor = deltaDict['largestChangeId']
            with open(driveRC.CURSOR, 'w') as cursor_file:
                pickle.dump(driveRC.deltaCursor, cursor_file)
            # Save client deletes/downloads
            driveRC.clientFileMan.addToDoDeletes(clientDelete)
            driveRC.clientFileMan.addToDoDownloads(clientDownload)
            # Clear ignoreList
            self.clearIgnoreList()

    def loadIgnoreList(self):
        ignoreList = []
        try:
            with open(driveRC.DRIVEIGNORE, 'r') as drive_ignore:
                ignoreList = pickle.load(drive_ignore)
        except:
            print '----------------------------------------'
            print 'Couldnt load ignore list'
        return ignoreList

    def clearIgnoreList(self):
        ignoreList = []
        with open(driveRC.DRIVEIGNORE, 'wb') as drive_ignore:
            pickle.dump(ignoreList, drive_ignore)
