import time
import pickle


class fileMan:

    CLIENTINDEX = 'clientIndex.pickle'  # Of type [theIndex, changeID]
    CHANGEID = 'clientChangeID.pickle'
    USEDINDEX = 'usedClientIndex.pickle'

    def __init__(self):
        print '----------------------------------------'
        print 'Local File Manager Initialised'

    def loadIndex(self):
        # Loads the client index fie and returns index itself, no change ID.
        indexAndId = []
        clientIndex = {}
        try:
            with open(fileMan.CLIENTINDEX, 'r') as the_index:
                indexAndId = pickle.load(the_index)
        except:
            print 'Cloudnt load client index'
            time.sleep(2)
            return self.loadIndex()
        clientIndex = indexAndId[0]
        return clientIndex

    def saveUsedIndex(self, theIndex):
        try:
            with open(fileMan.USEDINDEX, 'wb') as used_index:
                pickle.dump(theIndex, used_index)
        except:
            print '----------------------------------------'
            print 'Couldnt save used index, will try again'
            time.sleep(1)
            self.saveUsedIndex(theIndex)

    def getUsedIndex(self):
        theIndex = {}
        try:
            with open(fileMan.USEDINDEX, 'r') as used_index:
                theIndex = pickle.load(used_index)
        except:
            print '----------------------------------------'
            print 'Couldnt load used index, will try again'
            time.sleep(2)
            self.getUsedIndex()
        return theIndex

    def getIndexID(self):
        # Load the client index file and returns the change ID
        # Loads the client index fie and returns index itself, no change ID.
        indexAndId = []
        theID = None
        try:
            with open(fileMan.CLIENTINDEX, 'r') as the_index:
                indexAndId = pickle.load(the_index)
        except:
            print '----------------------------------------'
            print 'Couldnt load client index id'
            time.sleep(1)
            return self.getIndexID()
        theID = indexAndId[1]
        return theID

    def saveUsedID(self, theID):
        # Save a value as the last used ID
        try:
            with open(fileMan.CHANGEID, 'wb') as the_id:
                pickle.dump(theID, the_id)
        except:
            print '----------------------------------------'
            print 'Couldnt save last change id'
            time.sleep(2)
            self.saveUsedID(theID)

    def saveToDo(self, theList):
        # Save the client to-do list
        # Should be of type [[toUpload], {toDownload}, [toDelete]]
        try:
            with open('clientToDo.pickle', 'wb') as client_to_do:
                pickle.dump(theList, client_to_do)
        except:
            print '----------------------------------------'
            print 'Couldnt save to-do, will try again'
            time.sleep(1)
            self.saveToDo(theList)

    def loadToDo(self):
        # Load the client to-do list
        theList = []
        try:
            with open('clientToDo.pickle', 'r') as client_to_do:
                theList = pickle.load(client_to_do)
        except:
            print '----------------------------------------'
            print 'Couldnt load client to-do list'
            time.sleep(2)
            return self.loadToDo()
        return theList

    def addToDoDeletes(self, lowPaths):
        # Takes an array of paths to add to the delete list
        toDo = self.loadToDo()
        toDelete = toDo[2]
        for aPath in lowPaths:
            toDelete.append(aPath)
            print '----------------------------------------'
            print aPath + ' added to client delete list'
        newList = [toDo[0], toDo[1], toDelete]
        self.saveToDo(newList)

    def addToDoUploads(self, lowPaths):
        # Takes an array of paths to add to the upload list
        toDo = self.loadToDo()
        toUpload = toDo[0]
        for aPath in lowPaths:
            toUpload.append(aPath)
            print '----------------------------------------'
            print aPath + ' added to client upload list'
        newList = [toUpload, toDo[1], toDo[2]]
        self.saveToDo(newList)

    def addToDoDownloads(self, upperSourceDict):
        toDo = self.loadToDo()
        toDownload = toDo[1]
        for upperPath, source in upperSourceDict.iteritems():
            toDownload[upperPath] = source
            print '----------------------------------------'
            print upperPath + ' added to client download list'
        newList = [toDo[0], toDownload, toDo[2]]
        self.saveToDo(newList)

    def clearToDo(self):
        # Empty the to-do list
        newList = [[], {}, []]
        self.saveToDo(newList)
        print '----------------------------------------'
        print 'Client ToDo list cleared'

    def getUsedID(self):
        ''' When an index's change ID is used, it gets saved to CHANGEID
            as an old ID for future index lookups to compare against.
            This returns the stored (newest) change ID Defaults to
            0 if none found.'''
        theID = None
        try:
            with open(fileMan.CHANGEID, 'r') as change_id:
                theID = pickle.load(change_id)
            return theID
        except:
            print '----------------------------------------'
            print 'Cloudnt load used client id'
            return 0

    def indexSplit(self, index):
        ''' Divide the index into two indexes - one for Dropbox and one for Drive
            returns a list with [clientDropIndex, clientDriveIndex]
            index looks like {lowPath = [lastModified,
                                         casePath,
                                         baseLocation,
                                         destination]} to start. '''
        dropIndex = {}
        driveIndex = {}
        for lowerName, theMeta in index.iteritems():
            destination = theMeta[3]
            if destination == 'dropbox':
                # Only for Dropbox
                dropIndex[lowerName] = theMeta
            elif destination == 'drive':
                # Only for Drive
                driveIndex[lowerName] = theMeta
            else:
                # destination is 'dropdrive'. Add to both
                dropIndex[lowerName] = theMeta
                driveIndex[lowerName] = theMeta
        splitList = [dropIndex, driveIndex]
        return splitList
