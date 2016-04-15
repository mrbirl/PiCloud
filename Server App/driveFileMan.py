import os
import time
import pickle
import calendar
import mimetypes
from apiclient.http import MediaFileUpload


class driveFileMan:

    client = None
    driveLocalDirectory = ''
    userName = None
    INDEX = 'googleDriveIndex.pickle'

    def __init__(self, directory, theClient):
        driveFileMan.client = theClient
        driveFileMan.driveLocalDirectory = directory
        aboutStuff = driveFileMan.client.about().get().execute()
        driveFileMan.userName = aboutStuff['name']

    def pathBuilder(self, fileID, fileName=None):
        # Builds then returns the path for a file, via remote calls
        # filename parameter only passed by recursive call,
        # no need for initial call
        theFileName = fileName
        theFileID = fileID
        if theFileName is None:
            theFileName = self.getFileName(theFileID)
        # Check for a parent
        fileParents = driveFileMan.client.parents().list(fileId=theFileID).execute()
        parentItems = fileParents['items']
        for parentItem in parentItems:
            parentID = parentItem['id']
            isRoot = parentItem['isRoot']
            if isRoot:
                return theFileName
            else:
                # Get the title
                parentDeets = driveFileMan.client.files().get(fileId=parentID).execute()
                parentTitle = parentDeets['title']
                theFileName = parentTitle + '/' + theFileName
                theFileID = parentID
                # Recursively get all parents
                return self.pathBuilder(theFileID, fileName=theFileName)

    def getParentID(self, childID):
        # Given a file/folder ID, return list of parent ID's.
        parentsList = []
        parents = driveFileMan.client.parents().list(fileId = childID).execute()
        parentItems = parents['items']
        for parentItem in parentItems:
            parentID = parentItem['id']
            parentsList.append(parentID)
        return parentsList

    def findRemoteFile(self, localName, parentID=None):
        # Search Drive for a file. Returns a list of the file ID's (if
        # multiple files of same name) if it exists, None if it doesnt
        # Pass parent ID if known
        foundList = []
        isFound = False
        if parentID is None:
            fileList = driveFileMan.client.files().list().execute()
            items = fileList['items']
            for item in items:
                fileMime = item['mimeType']
                labels = item['labels']
                trashed = labels['trashed']
                if not trashed:
                    fileOwners = item['ownerNames']
                    for owner in fileOwners:
                        if driveFileMan.userName == owner:
                            fileID = item['id']
                            fileName = self.getFileName(fileID)
                            if str(localName) == str(fileName):
                                isFound = True
                                foundList.append(fileID)
            if isFound:
                return foundList
            else:
                return None
        else:
            # Parent ID passed, look for file with that parent
            foundList = []
            childList = driveFileMan.client.children().list(folderId = parentID).execute()
            childItems = childList['items']
            for item in childItems:
                childID = item['id']
                cTrashed = self.checkIfTrashed(childID)
                if not cTrashed:
                    childName = self.getFileName(childID)
                    if str(childName) == str(localName):
                        isFound = True
                        foundList.append(childID)
            if isFound:
                return foundList
            else:
                return None

    def checkIfTrashed(self, fileID):
        # Check if a file is trashed, returns true or false
        fileItem = driveFileMan.client.files().get(fileId=fileID).execute()
        labels = fileItem['labels']
        isTrashed = labels['trashed']
        if isTrashed:
            return True
        else:
            return False

    def createRemoteFolder(self, folderName, parentID=None):
        # Create a folder on Drive, returns the newely created folders ID
        body = {
            'title': folderName,
            'mimeType': "application/vnd.google-apps.folder"
        }
        if parentID:
            body['parents'] = [{'id': parentID}]
        root_folder = driveFileMan.client.files().insert(body=body).execute()
        return root_folder['id']

    def checkRoot(self, fileID):
        # Given a file ID, check if that file is in the Drive root folder
        # Return True if file is in root, otherwise False
        fileParents = driveFileMan.client.parents().list(fileId=fileID).execute()
        parentItems = fileParents['items']
        root = False
        for parentItem in parentItems:
            parentID = parentItem['id']
            isRoot = parentItem['isRoot']
            if isRoot:
                root = True
        return root

    def buildRemotePath(self, relPath):
        # Given the relative local path to a file, this makes the
        # necessary remote folders. Checks if each part exists, starting
        # at base. Returns the ID of the last folder
        print '----------------------------------------'
        print 'Building Drive remote path for ' + relPath
        # First take the file off the path, only interested in folders
        # Break path into array
        pathArray = []
        for pathPiece in relPath.split('/'):
            pathArray.append(pathPiece)
        pathArray.reverse()
        pathArray.pop(0)  # Remove filename from path
        pathArray.reverse()
        # For each item, check if it exists, create it if needed, get ID,
        # create next with parent pervious. start by checking if base in root
        pathStart = pathArray.pop(0)  # Pop it so can iter over rest of array without hitting this again
        pathStartID = self.findRemoteFile(pathStart)
        if pathStartID is not None:
            pathStartID = pathStartID[0]
            # Root exists,  check if it is Drive's root
            inRoot = self.checkRoot(pathStartID)
            if not inRoot:
                # Not in root, so not the same, create it
                startFolderID = self.createRemoteFolder(pathStart)
        if pathStartID is None:
            # Root of path doesn't exist. Make it.
            pathStartID = self.createRemoteFolder(pathStart)
        # Root folder now on Drive. Create all sub folders if they don't exist
        currentParent = pathStartID  # Make folder in last folder made. Inits at root folder
        for aFolder in pathArray:
            # print 'Current parent is ' + currentParent
            remoteID = self.findRemoteFile(aFolder, parentID=currentParent)
            if remoteID is None:
                thisFoldersID = self.createRemoteFolder(aFolder,
                                                        parentID=currentParent)
                currentParent = thisFoldersID  # Set current parent to this folder so next one is made in this one
            else:
                currentParent = remoteID[0]
        # Done. Return the currentParent ID which is the last folder made
        # print 'Last file made in pathbuild was ' + str(self.getFileName(currentParent))
        return currentParent

    def getFileName(self, fileID):
        # via remote calls
        # Given a fileID return the filename with extension - eg theFile.txt
        # If google docs files are passed, optionally can pass in the
        # desired type for the file to be converted
        fileExtension = ''
        fileObject = driveFileMan.client.files().get(fileId=fileID).execute()
        fileMime = fileObject['mimeType']
        if 'application/vnd.google-apps' in fileMime:
            # Google doc to download, get export type
            if fileMime == 'application/vnd.google-apps.document':
                # Download as MS Word file type
                fileExtension = '.docx'
            if fileMime == 'application/vnd.google-apps.spreadsheet':
                # Download as MS Excel file type
                fileExtension = '.xlsx'
            if fileMime == 'application/vnd.google-apps.drawing':
                # Download as JPEG
                fileExtension = '.jpg'
            if fileMime == 'application/vnd.google-apps.presentation':
                # Download as MS Powerpoint
                fileExtension = '.ppt'
        fileObject = driveFileMan.client.files().get(fileId=fileID).execute()
        baseName = fileObject['title']
        fullName = baseName + fileExtension
        return fullName

    def getIndex(self):
        # Load the index from file and return the dict
        try:
            with open(driveFileMan.INDEX, 'r') as the_index:
                theIndex = pickle.load(the_index)
            return theIndex
        except:
            print '----------------------------------------'
            print 'Couldnt load drive index.'
            return None

    def uploadFile(self, casePath):
        # Upload a file to Drive
        fullPath = self.getFullPath(casePath)
        fileName = os.path.basename(fullPath)
        mimeType = mimetypes.guess_type(fullPath)
        mimeType = mimeType[0]
        # Build the path
        try:
            parentFolderID = self.buildRemotePath(casePath)
        except:
            # Path build failed. No path. Root is parent
            parentFolderID = 'root'
        # Check if file is on server with that parent
        # Returns list of files or None
        remoteVersions = self.findRemoteFile(fileName, parentID=parentFolderID)
        if remoteVersions is not None:
            # Versions of this file exist in that folder,
            # so delete those before uploading
            for existingID in remoteVersions:
                try:
                    driveFileMan.client.files().delete(fileId=existingID).execute()
                    print '----------------------------------------'
                    print 'Existing version deleted'
                except:
                    print '----------------------------------------'
                    print 'Couldnt delete existing version'
        # Now we have the parent ID,
        # and any existing ones deleted. Ready to upload
        if os.path.getsize(fullPath) > 5*2**20:
            media_body = MediaFileUpload(fullPath,
                                         mimetype=mimeType,
                                         chunksize=1024*1024,
                                         resumable=True)
        else:
            media_body = MediaFileUpload(fullPath, mimetype=mimeType)
        body = {
            'title': fileName,
            'mimeType': mimeType
        }
        body['parents'] = [{'id': parentFolderID}]
        uploadedFile = driveFileMan.client.files().insert(
                body=body,
                media_body=media_body).execute()
        print '----------------------------------------'
        print str(fileName) + ' uploaded to Drive'

    def getFullPath(self, casePath):
        # Given a path return the full local path
        fullPath = os.path.join(driveFileMan.driveLocalDirectory, casePath)
        return fullPath

    def downloadFile(self, fileID, ignoreList=[]):
        # Download a file. For an ID, checks if Google Doc or normal
        # If normal, gets download link and location then downloads
        # If google doc, gets export link, then same as above
        # Return true if downloaded, otherwise false

        fileObject = driveFileMan.client.files().get(fileId=fileID).execute()
        fileMime = fileObject['mimeType']
        if 'application/vnd.google-apps' in fileMime:
            # Google doc to download, get export type
            if fileMime == 'application/vnd.google-apps.document':
                # Download as MS Word file type
                downloadLink = fileObject['exportLinks']['application/vnd.openxmlformats-officedocument.wordprocessingml.document']
            if fileMime == 'application/vnd.google-apps.spreadsheet':
                # Download as MS Excel file type
                downloadLink = fileObject['exportLinks']['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
            if fileMime == 'application/vnd.google-apps.drawing':
                # Download as JPEG
                downloadLink = fileObject['exportLinks']['image/jpeg']
            if fileMime == 'application/vnd.google-apps.presentation':
                # Download as MS Powerpoint file type
                downloadLink = fileObject['exportLinks']['application/vnd.openxmlformats-officedocument.presentationml.presentation']
        else:
            # Get file download URL
            downloadLink = fileObject.get('downloadUrl')
        # Get the local path
        fileMeta = self.getMetaByID(fileID)
        if fileMeta is None:
            return False
        filePath = fileMeta[1]
        # Get the full download path
        fullPath = self.joinFilePath(driveFileMan.driveLocalDirectory, filePath)  # Full download path including file
        relPath = os.path.dirname(os.path.realpath(fullPath))  # Full path without the file on the end
        if not os.path.exists(relPath):
            os.makedirs(relPath, 0777)
        # Download the file
        if downloadLink:
            resp, content = driveFileMan.client._http.request(downloadLink)
            if resp.status == 200:
                # print 'Status: %s' % resp
                # Write the content to a file in the correct location
                with open(fullPath, 'w') as the_file:
                    the_file.write(content)
                print '----------------------------------------'
                print 'Downloaded file: ' + str(filePath)
                return True
            else:
                print '----------------------------------------'
                print 'An error occurred: %s' % resp
                return False
        else:
            print '----------------------------------------'
            print 'No download link available, file cant be downloaded'
            return False

    def deleteRemote(self, lowPath):
        fileID = self.getFileID(lowPath)
        if fileID is not None:
            try:
                driveFileMan.client.files().trash(fileId=fileID).execute()
                print '----------------------------------------'
                print 'Deleted ' + str(lowPath) + ' from Drive'
            except:
                print '----------------------------------------'
                print 'Couldnt delete file from Drive'
        else:
            print '----------------------------------------'
            print 'Couldnt get a file ID'

    def getFileID(self, lowPath):
        # Get the ID of a file, given the lowPath
        theIndex = self.getIndex()
        theID = None
        for aLow, meta in theIndex.iteritems():
            if aLow == lowPath:
                try:
                    theID = meta[2]
                except:
                    # No file ID in the local index
                    # Check remotely
                    theID = self.findIdByRemote(lowPath)
        return theID

    def findIdByRemote(self, theLowPath):
        resultID = None
        pollResult = driveFileMan.client.files().list().execute()
        items = pollResult['items']
        for item in items:
            fileMime = item['mimeType']
            if fileMime != 'application/vnd.google-apps.folder':
                fileLabels = item['labels']
                fileTrashed = fileLabels['trashed']
                if not fileTrashed:
                    fileOwners = item['ownerNames']
                    for owner in fileOwners:
                        if owner == driveFileMan.userName:
                            fileID = item['id']
                            casePath = self.pathBuilder(fileID)
                            casePath = self.formatPath(casePath)
                            lowerPath = casePath.lower()
                            if theLowPath == lowerPath:
                                resultID = fileID
        return resultID

    def deleteLocal(self, driveIndex, fileID):
        # Delete a local file. Pass in the driveIndex and either
        # the lowerRelPath *OR* the fileID
        # Return true if file deleted, false if it still exists
        # Deletes file from storage then driveIndex
        fileName = driveIndex.getPathById(fileID)
        if fileName is not None:
            # File name was found in the index
            fullPath = self.joinFilePath(driveFileMan.driveLocalDirectory,
                                         fileName)
            if os.path.exists(fullPath):
                try:
                    os.remove(fullPath)
                except:
                    print '----------------------------------------'
                    print 'Couldnt local remove file'
                    pass
                # If file not found now, return true
                if not os.path.exists(fullPath):
                    print '----------------------------------------'
                    print 'Local file deleted'
                    return True
                # If file still exists, return false
                if os.path.exists(fullPath):
                    print '----------------------------------------'
                    print 'Local file not deleted'
                    return False
            else:
                return True  # Because although it wasn't deleted, it doesnt exist
                print '----------------------------------------'
                print 'File not found in Index, cant delete'

    def convertTime(self, driveTime):
        # Convert from drive time (RFC3339) to local time (seconds since epoch)
        theTime = str(driveTime)
        if theTime.endswith("Z"):
            # No offset (00:00)
            utcLastModified = time.strptime(theTime, '%Y-%m-%dT%H:%M:%S.%fZ')
        else:
            # Offset on the utcLastModified
            end = time.strptime(theTime, '%Y-%m-%dT%H:%M:%S.%f%z')
        theTime = calendar.timegm(utcLastModified)
        return theTime

    def formatPath(self, path):
        entryPath = str(path)
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

    def joinFilePath(self, directory, filePath):
        fullPath = os.path.join(directory, filePath)
        return fullPath

    def getMetaByID(self, fileID):
        # Given a files ID, return [modTime, casePath] by asking Drive
        item = driveFileMan.client.files().get(fileId=fileID).execute()
        fileMime = item['mimeType']
        if fileMime != 'application/vnd.google-apps.folder':
            fileLabels = item['labels']
            fileTrashed = fileLabels['trashed']
            if not fileTrashed:
                fileOwners = item['ownerNames']
                for owner in fileOwners:
                    if owner == driveFileMan.userName:
                        fullPath = self.pathBuilder(fileID)
                        fullPath = self.formatPath(fullPath)
                        lowerPath = fullPath.lower()
                        modTime = item.get('modifiedDate')
                        modTime = self.convertTime(modTime)
                        theMeta = [modTime, fullPath]
                        return theMeta
                    else:
                        return None
            else:
                return None
        else:
            # print 'Its a folder, not downloading'
            return None
