import pickle
import os
import time


class localFileMan:

    INDEX = 'localIndex.pickle'
    MONITORED = 'monitoredPaths.pickle'
    DELETED = 'localDeletes.pickle'
    deleted = None

    def __init__(self):
        print '----------------------------------------'
        print 'Local file manager created'

    def compareIndex(self, index1, index2):
        # Returns dictionary of elements in index 1 that aren't in index 2
        differences = {}
        for aPath, someMeta in index1:
            found = False
            for secondPath, moreMeta in index2:
                if aPath == secondPath:
                    found = True
            if found is False:
                differences[aPath] = someMeta

    def changePathPermissions(self):
        print '----------------------------------------'
        print 'Changing File & Folder Permissions'
        paths = self.loadPaths()
        for path, destination in paths.iteritems():
            for dirpath, dirnames, filenames in os.walk(path):
                # os.chmod(dirpath, 0755)
                for filename in filenames:
                    filePath = os.path.join(dirpath, filename)
                    os.chmod(filePath, 0755)

    def addFile(self, fullPath, passedModTime=None):
        # Add a file to the index. If modTime passed use that instead.
        if not os.path.isdir(fullPath):
            if '.DS_Store' not in fullPath:
                monitoredPath = self.getMonitored(fullPath)
                if monitoredPath.endswith('/'):
                    monitoredPath = monitoredPath[:-1]
                if monitoredPath == '/Users/Cian/Downloads/Misc Dropbox Files':
                    self.addMiscItem(fullPath)
                elif monitoredPath == '/Users/Cian/Downloads/Misc Drive Files':
                    self.addMiscItem(fullPath)
                else:
                    destination = self.getDestination(monitoredPath)
                    baseLocation = os.path.dirname(monitoredPath)
                    casePath = os.path.relpath(fullPath, baseLocation)
                    lowerPath = casePath.lower()
                    if passedModTime is None:
                        modTime = os.path.getmtime(fullPath)
                    else:
                        modTime = passedModTime
                    theMeta = [modTime, casePath, baseLocation, destination]
                    theIndex = self.loadIndex()
                    theIndex[lowerPath] = theMeta
                    self.pickleIndex(theIndex)
                    print '----------------------------------------'
                    print '*** Added file ' + casePath + ' to index ***'

    def addMiscItem(self, fullPath):
        # For miscelanious files downloaded to default folder,
        # add then to the index without the monitoring folder on the file name
        monitoredPath = self.getMonitored(fullPath)
        if monitoredPath.endswith('/'):
            monitoredPath = monitoredPath[:-1]
        destination = self.getDestination(monitoredPath)
        casePath = os.path.relpath(fullPath, monitoredPath)
        lowerPath = casePath.lower()
        modTime = os.path.getctime(fullPath)
        theMeta = [modTime, casePath, monitoredPath, destination]
        theIndex = self.loadIndex()
        theIndex[lowerPath] = theMeta
        self.pickleIndex(theIndex)
        print '----------------------------------------'
        print '*** Added misc file ' + casePath + ' to index ***'

    def changeModTime(self, lowPath, newMod):
        # Changes the mod time of a file. Returns True if it worked
        theIndex = self.loadIndex()
        newMeta = None
        for aFile, someMeta in theIndex.iteritems():
            if aFile == lowPath:
                casePath = someMeta[1]
                monPath = someMeta[2]
                destination = someMeta[3]
                newMeta = [newMod, casePath, monPath, destination]
        if newMeta is not None:
            theIndex[lowPath] = newMeta
            return True
        else:
            return False

    def removeFile(self, fullPath):
        # Remove a file from the index
        casePath = self.getFileName(fullPath)
        lowerPath = casePath.lower()
        theIndex = self.loadIndex()
        del theIndex[lowerPath]
        print '----------------------------------------'
        print '*** Removed file ' + casePath + ' from Index ***'
        self.pickleIndex(theIndex)

    def deleteFiles(self, removeList):
        # Deletes all files in removeList from the local machine
        # Expects a list of lowPaths
        for aFile in removeList:
            try:
                fullPath = self.getFullPath(aFile)
                os.remove(fullPath)
                self.removeFile(fullPath)
                print '----------------------------------------'
                print 'Deleted file ' + str(aFile)
            except:
                self.secondDelete(aFile)

    def secondDelete(self, aFile):
        try:
            aFile = aFile.lower()
            fullPath = self.getFullPath(aFile)
            os.remove(fullPath)
            self.removeFile(fullPath)
            print '----------------------------------------'
            print 'File ' + aFile + ' deleted'
        except:
            print '----------------------------------------'
            print 'Couldnt delete ' + aFile

    def getFullPath(self, lowPath):
        # Given a lower case relPath, get the full path to that file
        localIndex = self.loadIndex()
        fileMeta = localIndex[lowPath]
        casePath = fileMeta[1]
        baseLocation = fileMeta[2]
        fullPath = os.path.join(baseLocation, casePath)
        return fullPath

    def getMonitored(self, fullPath):
        # Given a full path to a file, return
        # the monitored location it belongs to
        baseLocation = None
        monitoredPaths = self.loadPaths()
        for basePath, destination in monitoredPaths.iteritems():
            if basePath in fullPath:
                baseLocation = basePath
        return baseLocation

    def getDestination(self, monitoredPath):
        # Given a monitored path, return the sync
        # destination (dropbox, drive, both)
        destination = None
        monitoredPaths = self.loadPaths()
        for aBase, aDest in monitoredPaths.iteritems():
            if monitoredPath in aBase:
                destination = aDest
        return destination

    def getFileName(self, fullPath):
        # Give a file path, return the casePath
        monitoredPath = self.getMonitored(fullPath)
        if monitoredPath.endswith('/'):
            monitoredPath = monitoredPath[:-1]
        destination = self.getDestination(monitoredPath)
        baseLocation = os.path.dirname(monitoredPath)
        casePath = os.path.relpath(fullPath, baseLocation)
        return casePath

    def getCasePath(self, lowPath):
        # Given a lowercase path, find and return the case-sensitive version
        theIndex = self.loadIndex()
        casePath = None
        for aLow, meta in theIndex.iteritems():
            if aLow == lowPath:
                casePath = meta[1]
        return casePath

    def formatPathRemote(self, fullPath):
        # Convert path to one suitable for the server
        entryPath = str(fullPath)
        slashStart = True
        while slashStart:
            if entryPath.startswith("/"):
                entryPath = entryPath[1:]
            else:
                slashStart = False
        if ' ' in entryPath:
            entryPath.replace(" ", "\\ ")
        if "\\" in entryPath:
            entryPath = entryPath.replace("\\", "/")
        return entryPath

    def loadIndex(self):
        # Returns the index
        theIndex = {}
        try:
            with open(localFileMan.INDEX, 'r') as the_index:
                theIndex = pickle.load(the_index)
            return theIndex
        except:
            print '----------------------------------------'
            print 'Couldnt load index, will try again'
            time.sleep(2)
            return self.loadIndex()

    def pickleIndex(self, index):
        # Saves the index
        theIndex = index
        try:
            with open(localFileMan.INDEX, 'wb') as index_file:
                pickle.dump(theIndex, index_file)
        except:
            print '----------------------------------------'
            print 'Couldnt save index, will try again'
            time.sleep(1)
            return self.pickleIndex(theIndex)

    def loadDeleted(self):
        # Loads and returns the deleted list
        try:
            with open(self.DELETED, 'r') as deleted_list:
                localFileMan.deleted = pickle.load(deleted_list)
        except:
            localFileMan.deleted = []
            with open(self.DELETED, 'wb') as deleted_list:
                pickle.dump(localFileMan.deleted, deleted_list)

    def loadPaths(self):
        # load and return the list of monitored paths
        thePaths = {}
        try:
            with open(localFileMan.MONITORED, 'r') as the_paths:
                thePaths = pickle.load(the_paths)
            return thePaths
        except:
            print '----------------------------------------'
            print 'Couldnt load paths, will try again'
            time.sleep(4)
            return self.loadPaths()

    def picklePaths(self, paths):
        thePaths = paths
        try:
            with open(localFileMan.MONITORED, 'wb') as paths_file:
                pickle.dump(thePaths, paths_file)
        except:
            print '----------------------------------------'
            print 'Couldnt save paths'
            time.sleep(2)
            self.picklePaths(thePaths)
