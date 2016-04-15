import os
import pickle
import paramiko
import localFileMan


class ftMan:

    ssh = None
    sftp = None
    serverAddress = None
    serverUsername = None
    serverPassword = None
    theFileMan = None
    theIndex = {}
    INDEX = 'localIndex.pickle'
    indexID = 0
    INDEXID = 'indexID.pickle'
    serverChangeList = []
    CHANGELIST = 'serverChangeList.pickle'

    def __init__(self, servAdd, uName, pwd):
        # Create SSH client
        ftMan.ssh = paramiko.SSHClient()
        # Handle keys
        ftMan.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ftMan.serverAddress = servAdd
        ftMan.serverUsername = uName
        ftMan.serverPassword = pwd
        ftMan.theFileMan = localFileMan.localFileMan()
        try:
            with open(ftMan.INDEXID, 'r') as index_id:
                ftMan.indexID = pickle.load(index_id)
        except:
            with open(ftMan.INDEXID, 'wb') as index_id:
                pickle.dump(ftMan.indexID, index_id)
            print '----------------------------------------'
            print 'Index ID file created'

    def connect(self):
        print '----------------------------------------'
        print 'Connecting to server...'
        ftMan.ssh.connect(ftMan.serverAddress,
                          username=ftMan.serverUsername,
                          password=ftMan.serverPassword)
        ftMan.sftp = ftMan.ssh.open_sftp()
        print 'Connected'

    def close(self):
        ftMan.sftp.close()
        ftMan.ssh.close()
        print '----------------------------------------'
        print 'Server connection closed'

    def download(self, downDict):
        # downDict is {casePath = source}, where source is 'dropbox' or 'drive'
        for aFile, source in downDict.iteritems():
            basePath = self.lookupDownDest(aFile, source)
            fullLocalPath = os.path.join(basePath, aFile)
            remotePath = '/home/' + ftMan.serverUsername + '/CloudDown/' + aFile
            localPath = os.path.dirname(fullLocalPath)
            if not os.path.exists(localPath):
                os.makedirs(localPath)
            print '----------------------------------------'
            print 'Downloading ' + aFile + ' to ' + fullLocalPath
            ftMan.sftp.get(remotePath, fullLocalPath)
            print 'Downloaded'

    def lookupDownDest(self, casePath, source):
        ''' Given a case sensitive relPath and its remote source (dropbox, drive)
        look for a monitored path this file belongs to. If none can be
        determined, default to a Dropbox or Drive catchall folder first element
        of casePath should be last part of a monitored path.'''

        monitoredPaths = self.theFileMan.loadPaths()
        localGoTo = None
        for monPath, monDest in monitoredPaths.iteritems():
            if monDest == source:
                pathArray = []
                # Get monitored folder
                if monPath.endswith('/'):
                    monPath = monPath[:-1]
                # To compare to remote base folder name
                monFolder = os.path.basename(monPath)
                pathMinusMonFolder = os.path.dirname(monPath)
                # Get base of filePath
                for pathPiece in casePath.split('/'):
                    pathArray.append(pathPiece)
                # The base of the files path
                remoteBase = pathArray[0]
                if monFolder == remoteBase:
                    # This remote file belongs in this monitored folder
                    localGoTo = pathMinusMonFolder
            else:
                # Destination could be 'dropdrive',
                # but source never will be one or the other
                # Check if base folder is 'dropdrive' monitored location
                forDropDrive = self.dropdriveCheck(casePath)
                if forDropDrive:
                    # Source is 'dropdrive'
                    pathArray = []
                    # Get monitored folder
                    if monPath.endswith('/'):
                        monPath = monPath[:-1]
                    # To compare to remote base folder name
                    monFolder = os.path.basename(monPath)
                    pathMinusMonFolder = os.path.dirname(monPath)
                    # Get base of filePath
                    for pathPiece in casePath.split('/'):
                        pathArray.append(pathPiece)
                    # The base of the files path
                    remoteBase = pathArray[0]
                    if monFolder == remoteBase:
                        # This remote file belongs in this monitored folder
                        localGoTo = pathMinusMonFolder
        if localGoTo is None:
            if source == 'dropbox':
                localGoTo = '/Users/Cian/Downloads/Misc Dropbox Files/'
            else:
                localGoTo = '/Users/Cian/Downloads/Misc Drive Files/'
        return localGoTo

    def dropdriveCheck(self, casePath):
        # Given a casePath, determine, via basename,
        # if it is a 'dropdrive' monitored location
        monitoredPaths = self.theFileMan.loadPaths()
        isDropDrive = False
        for aPath, aDestination in monitoredPaths.iteritems():
            if aDestination == 'dropdrive':
                if aPath.startswith('/'):
                    aPath = aPath[1:]
                monArray = []
                for monPiece in aPath.split('/'):
                    monArray.append(monPiece)
                monArray.reverse()
                caseArray = []
                for casePiece in casePath.split('/'):
                    caseArray.append(casePiece)
                if monArray[0] == caseArray[0]:
                    isDropDrive = True
        return isDropDrive

    def upload(self, upList):
        # Expects a list of lowerRel paths
        for aFile in upList:
            doUpload = True
            try:
                localFile = ftMan.theFileMan.getFullPath(aFile)
            except:
                doUpload = False
            if doUpload:
                remoteFile = ftMan.theFileMan.getCasePath(aFile)
                remoteFile = ftMan.theFileMan.formatPathRemote(remoteFile)
                remoteFile = '/home/' + ftMan.serverUsername + '/CloudDown/'+ remoteFile
                remotePath = os.path.dirname(remoteFile)
                try:
                    dirListing = ftMan.sftp.listdir(path=remotePath)
                    ftMan.sftp.put(localFile, remoteFile)
                    print '----------------------------------------'
                    print 'Uploaded ' + aFile
                except:
                    print '----------------------------------------'
                    print 'Couldnt list...'
                    self.mkDirectory(remotePath)
                    print 'Remote directory made'
                    ftMan.sftp.put(localFile, remoteFile)
                    print 'Uploaded ' + aFile

    def uploadIndex(self):
        # Upload the index and callID to the server
        # Then increment the callID for next time
        with open(ftMan.INDEX, 'r') as the_index:
            ftMan.theIndex = pickle.load(the_index)
        with open(ftMan.INDEXID, 'r') as index_id:
            ftMan.indexID = pickle.load(index_id)
        indexAndIDCombo = [ftMan.theIndex, ftMan.indexID]
        INDEXIDCOMBO = 'indexAndIDCombo.pickle'
        with open(INDEXIDCOMBO, 'wb') as index_id_combo:
            pickle.dump(indexAndIDCombo, index_id_combo)
        remoteFile = '/home/' + ftMan.serverUsername + '/PiCloud/clientIndex.pickle'
        # Upload the file
        ftMan.sftp.put(INDEXIDCOMBO, remoteFile)
        # Increment the index ID
        ftMan.indexID += 1
        with open(ftMan.INDEXID, 'wb') as index_id:
            pickle.dump(ftMan.indexID, index_id)

    def downloadChangeList(self):
        # Download the list of changes to be made (includes change ID)
        remotePath = '/home/' + ftMan.serverUsername + '/PiCloud/clientToDo.pickle'
        ftMan.sftp.get(remotePath, ftMan.CHANGELIST)

    def mkDirectory(self, remotePath):
        # Make the directory for the file path passed in
        try:
            makeCommand = 'mkdir -p "' + remotePath + '"'
            ftMan.ssh.exec_command(makeCommand)
        except:
            print '----------------------------------------'
            print 'Couldnt make directory'
