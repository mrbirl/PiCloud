import auth
import pickle
import dropFileMan as dropFileMan


class dropIndex:

    # Build and maintain Dropbox index

    client = auth.getClient()

    theIndex = {}

    theDirectory = ''

    dropFileMan = None

    CURSOR = 'deltaCursor.pickle'
    INDEX = 'dropboxIndex.pickle'

    deltaDict = None
    deltaCursor = None

    def __init__(self, directory):
        # Initialise the class
        dropIndex.theDirectory = directory
        dropIndex.dropFileMan = dropFileMan.dropFileMan(directory)
        try:
            with open(dropIndex.INDEX, 'r') as the_index:
                dropIndex.theIndex = pickle.load(the_index)
            print '----------------------------------------'
            print 'Dropbox Index loaded'
        except:
            self.build()
            print '----------------------------------------'
            print 'Index built'
            with open(dropIndex.CURSOR, 'w') as cursor_file:
                pickle.dump(dropIndex.deltaCursor, cursor_file)
            with open(dropIndex.INDEX, 'w') as index_file:
                pickle.dump(dropIndex.theIndex, index_file)

    def build(self):
        # Build index from scratch
        dropIndex.deltaDict = dropIndex.client.delta()
        dropIndex.deltaCursor = dropIndex.deltaDict['cursor']
        deltaEntries = dropIndex.deltaDict['entries']
        for entry in deltaEntries:
            entryMetaData = entry.pop(1)
            if entryMetaData is not None:
                entryIsDir = entryMetaData['is_dir']
                if not entryIsDir:
                    lastModified = entryMetaData['modified']
                    lastModified = dropIndex.dropFileMan.convertTime(lastModified)
                    casePath = str(entryMetaData['path'])  # Case sensitive
                    casePath = dropIndex.dropFileMan.formatPath(casePath)
                    lowerPath = entry.pop(0)
                    if lowerPath.startswith("/"):
                        lowerPath = lowerPath[1:]
                    localMeta = [lastModified, casePath]
                    dropIndex.theIndex[lowerPath] = localMeta
                    # Download the file
                    dropIndex.dropFileMan.download(casePath)

    def add(self, upperRel, dropModTime, sourceRemote=False):
        # Add a file to the index
        # Source remote is True if this addition is not because of a
        # a change on the Dropbox server
        print '----------------------------------------'
        print 'Adding file ' + str(upperRel) + ' to Dropbox Index'
        dropIndex.dropFileMan.formatPath(upperRel)
        try:
            # Convert dropbox time to local time
            dropModTime = dropIndex.dropFileMan.convertTime(dropModTime)
        except:
            # Couldn't convert time, probably already converted
            pass
        newMeta = [dropModTime, upperRel]
        lowerPath = upperRel.lower()
        slashStart = True
        while slashStart:
            if lowerPath.startswith("/"):
                lowerPath = lowerPath[1:]
            else:
                slashStart = False
        dropIndex.theIndex[lowerPath] = newMeta
        if sourceRemote:
            dropIndex.dropFileMan.upload(upperRel)
        self.pickleIndex()

    def delete(self, relPath):
        # Delete file from the index
        # Takes an upper or lower rel path. Recommend formatPath first.
        lowerPath = relPath.lower()
        lowerPath = dropIndex.dropFileMan.formatPath(lowerPath)
        if lowerPath.startswith("/"):
            lowerPath = lowerPath[1:]
        del dropIndex.theIndex[lowerPath]

    def printIndex(self):
        # Print the index in a readable format
        print dropIndex.theIndex

    def pickleIndex(self):
        with open(dropIndex.INDEX, 'wb') as index_file:
            pickle.dump(dropIndex.theIndex, index_file)

    def getModTime(self, filePath):
        filePath = str(filePath)
        if filePath.startswith("/"):
            filePath = filePath[1:]
        filePath = str(filePath)
        filePath = filePath.lower()
        metaData = dropIndex.theIndex[filePath]
        modTime = metaData[0]
        return modTime

    def getIndex(self):
        # Return the dict index
        return dropIndex.theIndex

    def getDirectory(self):
        # Return the directory
        return dropIndex.theDirectory

    def getServiceName(self):
        return 'dropbox'

    def getClient(self):
        return dropIndex.client
