import pickle
import auth
import dropFileMan
import localFileMan


class dropRC:

    # Check Dropbox for updates, update locally as needed

    client = auth.getClient()

    dropboxFileMan = None
    clientFileMan = None

    CURSOR = 'deltaCursor.pickle'
    deltaCursor = None

    DROPIGNORE = 'dropIgnore.pickle'

    def __init__(self, dropIndex):
        dropRC.dropboxFileMan = dropFileMan.dropFileMan(dropIndex.getDirectory())
        dropRC.clientFileMan = localFileMan.fileMan()
        # Get the cursor
        with open(dropRC.CURSOR, 'r') as the_cursor:
            dropRC.deltaCursor = pickle.load(the_cursor)

    def check(self, dropIndex):
        print '----------------------------------------'
        print '------ Checking Dropbox ------'
        clientDownload = {}  # Dict of files for client to download
        clientDelete = []  # List of files for client to delete
        deltaDict = dropRC.client.delta(dropRC.deltaCursor)
        deltaEntries = deltaDict['entries']
        ignoreList = self.loadIgnoreList()
        for entry in deltaEntries:
            remoteMeta = entry[1]
            remoteLowPath = entry[0]
            # File to remove
            if remoteMeta is None:
                # Delete file
                deleteOK = dropRC.dropboxFileMan.deleteLocal(remoteLowPath,
                                                             dropIndex.getIndex())
                if deleteOK:
                    # Update index
                    dropIndex.delete(remoteLowPath)
                    # save index
                    dropIndex.pickleIndex()
                    # Add to this client delete list
                    cDeletePath = dropRC.dropboxFileMan.formatPath(remoteLowPath)
                    clientDelete.append(cDeletePath)
            # File to add
            else:
                if remoteLowPath.startswith('/'):
                    remoteLowPath = remoteLowPath[1:]
                # Make sure it's a file not a folder
                isDirectory = remoteMeta['is_dir']
                if not isDirectory:
                    fileFound = False
                    # Search local index
                    for localLowPath, localMeta in dropIndex.getIndex().iteritems():
                        localModTime = localMeta[0]
                        remoteModTime = remoteMeta['modified']
                        remoteModTime = dropRC.dropboxFileMan.convertTime(remoteModTime)
                        remoteUpperPath = remoteMeta['path']
                        # File found locally
                        if localLowPath == remoteLowPath:
                            fileFound = True
                            # Compare Versions
                            # Local newer
                            if localLowPath not in ignoreList:
                                if localModTime > remoteModTime:
                                    upperPath = remoteUpperPath
                                    # Upload
                                    dropRC.dropboxFileMan.upload(upperPath)
                                # Remote newer
                                if remoteModTime > localModTime:
                                    # Download
                                    dropRC.dropboxFileMan.download(remoteUpperPath)
                                    # Update index
                                    dropIndex.add(remoteUpperPath, remoteModTime)
                                    # Save index
                                    dropIndex.pickleIndex()
                                    # Add to this client download list
                                    cDownPath = dropRC.dropboxFileMan.formatPath(remoteUpperPath)
                                    clientDownload[cDownPath] = 'dropbox'
                    # This entry not found
                    if fileFound is False:
                        if remoteLowPath not in ignoreList:
                            print '----------------------------------------'
                            print 'Dropbox File Not Found In Local Dropbox Index'
                            # Download
                            dropRC.dropboxFileMan.download(remoteUpperPath)
                            # Update index
                            dropIndex.add(remoteUpperPath, remoteModTime)
                            # Save index
                            dropIndex.pickleIndex()
                            # Add to this client download list
                            cDownPath = dropRC.dropboxFileMan.formatPath(remoteUpperPath)
                            clientDownload[cDownPath] = 'dropbox'

        dropRC.deltaCursor = deltaDict['cursor']
        with open(dropRC.CURSOR, 'w') as cursor_file:
                pickle.dump(dropRC.deltaCursor, cursor_file)
        # Write client download/delete lists to file
        dropRC.clientFileMan.addToDoDeletes(clientDelete)
        dropRC.clientFileMan.addToDoDownloads(clientDownload)
        # Clear ignoreList
        self.clearIgnoreList()

    def loadIgnoreList(self):
        ignoreList = []
        try:
            with open(dropRC.DROPIGNORE, 'r') as drop_ignore:
                ignoreList = pickle.load(drop_ignore)
        except:
            print '----------------------------------------'
            print 'Couldnt load ignore list'
        return ignoreList

    def clearIgnoreList(self):
        ignoreList = []
        with open(dropRC.DROPIGNORE, 'wb') as drop_ignore:
            pickle.dump(ignoreList, drop_ignore)
