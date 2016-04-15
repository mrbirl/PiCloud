import pickle
import driveFileMan


class driveIndex:

    # Build and maintain Drive index
    userName = None

    client = None

    theIndex = {}

    theDirectory = ''

    driveFileMan = None

    INDEX = 'googleDriveIndex.pickle'
    CURSOR = 'driveCursor.pickle'

    deltaDict = None
    deltaCursor = None

    def __init__(self, directory, theClient):
        #  Initialise the class
        # Get user name
        driveIndex.client = theClient
        aboutStuff = driveIndex.client.about().get().execute()
        driveIndex.userName = aboutStuff['name']

        driveIndex.theDirectory = directory
        driveIndex.driveFileMan = driveFileMan.driveFileMan(directory,
                                                            driveIndex.client)
        try:
            with open(driveIndex.INDEX, 'r') as the_index:
                driveIndex.theIndex = pickle.load(the_index)
            print '----------------------------------------'
            print 'Drive Index loaded'
        except:
            print '----------------------------------------'
            print 'No Drive Index found, building one...'
            self.build()
            print '----------------------------------------'
            print 'Drive Index built'
            with open(driveIndex.CURSOR, 'w') as cursor_file:
                pickle.dump(driveIndex.deltaCursor, cursor_file)
            with open(driveIndex.INDEX, 'w') as index_file:
                pickle.dump(driveIndex.theIndex, index_file)

    def build(self):
        # Dict is of type {lowerCasePath = [modTime, casePath, ID]}
        driveIndex.theIndex = {}
        pollResult = driveIndex.client.files().list().execute()
        items = pollResult['items']
        for item in items:
            fileMime = item['mimeType']
            # If it's not a folder, build the path
            if fileMime != 'application/vnd.google-apps.folder':
                fileLabels = item['labels']
                fileTrashed = fileLabels['trashed']
                if not fileTrashed:
                    fileOwners = item['ownerNames']
                    for owner in fileOwners:
                        if owner == driveIndex.userName:
                            fileID = item['id']
                            fullPath = driveIndex.driveFileMan.pathBuilder(fileID)
                            fullPath = driveIndex.driveFileMan.formatPath(fullPath)
                            lowerPath = fullPath.lower()
                            modTime = item.get('modifiedDate')
                            modTime = driveIndex.driveFileMan.convertTime(modTime)
                            theMeta = [modTime, fullPath, fileID]
                            driveIndex.theIndex[lowerPath] = theMeta
                            print '-----------------------------------'
                            print 'Added to Drive Index: ' + fullPath
                            # Download the file
                            fileDownloaded = driveIndex.driveFileMan.downloadFile(fileID)
        # Get a delta cursor for the check later
        deltaDict = driveIndex.client.changes().list(includeDeleted=True).execute()
        driveIndex.deltaCursor = deltaDict['largestChangeId']

    def add(self, upperRel, driveModTime, fileID = None, sourceRemote = False):
        # Add a file to the index
        # sourceRemote determines where the add is from - if its
        # True it's not added because of a change on Drive, so file
        # should be uploaded to Drive.
        # fileID can be passed if adding from remote check.
        driveIndex.driveFileMan.formatPath(upperRel)
        try:
            # Convert dropbox time to local time
            driveModTime = driveIndex.driveFileMan.convertTime(driveModTime)
        except:
            # Couldn't convert time, already converted
            pass
        if fileID is None:
            newMeta = [driveModTime, upperRel]
        else:
            newMeta = [driveModTime, upperRel, fileID]
        lowerPath = upperRel.lower()
        slashStart = True
        while slashStart:
            if lowerPath.startswith("/"):
                lowerPath = lowerPath[1:]
            else:
                slashStart = False
        driveIndex.theIndex[lowerPath] = newMeta
        if sourceRemote:
            driveIndex.driveFileMan.uploadFile(upperRel)
        print '----------------------------------------'
        print 'File ' + str(upperRel) + ' added to Drive Index'
        self.pickleIndex()

    def delete(self, relPath):
        # Delete file from the index
        # Takes an upper or lower rel path. Recommend formatPath first.
        lowerPath = relPath.lower()
        lowerPath = driveIndex.driveFileMan.formatPath(lowerPath)
        if lowerPath.startswith("/"):
            lowerPath = lowerPath[1:]
        del driveIndex.theIndex[lowerPath]
        print '----------------------------------------'
        print 'Deleted file ' + str(relPath) + ' from Drive Index'

    def getPathById(self, fileID):
        # Get upper rel path by passing in ID
        for lower, meta in driveIndex.theIndex.iteritems():
            if str(meta[2]) == str(fileID):
                return meta[1]
        return None

    def getModTime(self, filePath):
        filePath = str(filePath)
        if filePath.startswith("/"):
            filePath = filePath[1:]
        filePath = str(filePath)
        filePath = filePath.lower()
        metaData = driveIndex.theIndex[filePath]
        modTime = metaData[0]
        return modTime

    def printIndex(self):
        # Print the index in a readable format
        for lower, meta in driveIndex.theIndex.iteritems():
            print '----------------------------------------'
            print lower
            print meta

    def pickleIndex(self):
        with open(driveIndex.INDEX, 'wb') as index_file:
            pickle.dump(driveIndex.theIndex, index_file)

    def getIndex(self):
        # Return the dict index
        return driveIndex.theIndex

    def getDirectory(self):
        # Return the directory
        return driveIndex.theDirectory

    def getServiceName(self):
        return 'drive'

    def getClient(self):
        return driveIndex.client
