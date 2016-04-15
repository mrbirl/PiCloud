import os
import time
import auth
import calendar
import pickle


class dropFileMan:

    client = auth.getClient()
    dropboxLocalDirectory = ''
    INDEX = 'dropboxIndex.pickle'

    def __init__(self, directory):
        dropFileMan.dropboxLocalDirectory = directory

    def download(self, casePath):
        directory = dropFileMan.dropboxLocalDirectory
        lowerPath = casePath.lower()
        directory = self.formatPath(directory)
        lowerPath = self.formatPath(lowerPath)
        casePath = self.formatPath(casePath)
        fullPath = self.joinFilePath(directory, casePath)
        destinationPath = os.path.dirname(os.path.realpath(fullPath))
        if not os.path.exists(destinationPath):
            os.makedirs(destinationPath, 0777)
        downloadOK = False
        with open(fullPath, 'w') as the_file:
            try:
                f = dropFileMan.client.get_file(lowerPath).read()
                the_file.write(f)
                downloadOK = True
            except:
                print '----------------------------------------'
                print 'Download failed...'
            # the_file.write(f)
        if downloadOK is False:
            os.remove(fullPath)
        if os.path.exists(fullPath):
            print '---------------------------'
            print 'Downloaded: ' + fullPath
        else:
            print '----------------------------------------'
            print 'Failed to Download: ' + casePath

    def upload(self, caseRelPath):
        caseRelPath = str(caseRelPath)
        caseRelPath = self.formatPath(caseRelPath)
        fullPath = self.joinFilePath(dropFileMan.dropboxLocalDirectory,
                                     caseRelPath)
        if not fullPath.startswith('/'):
            fullPath = '/' + fullPath
        f = open(fullPath)
        response = dropFileMan.client.put_file(caseRelPath, f, True)
        print '-----------------------'
        print 'Uploaded: ' + caseRelPath

    def getIndex(self):
        # Load the dropbox index from file
        try:
            with open(dropFileMan.INDEX, 'r') as the_index:
                theIndex = pickle.load(the_index)
            return theIndex
        except:
            print 'Couldnt load Dropbox index.'
            return None

    def deleteRemote(self, lowPath):
        if not lowPath.startswith('/'):
            lowPath = '/' + lowPath
        try:
            dropFileMan.client.file_delete(lowPath)
            print '----------------------------------------'
            print 'Deleted ' + lowPath + ' from Dropbox'
        except:
            # Most likely to happen if this delete happened on Dropbox already
            print '----------------------------------------'
            print lowPath + ' not deleted from Dropbox'

    def deleteLocal(self, lowerRelPath, dropboxIndex):
        # Delete a local item. Return True if file removed, false if not
        # Receives lower rel path from dropbox and no upper. Look for upper
        # in indexes then remove.
        # Expects the actual index dict, not the index object
        lowerRelPath = self.formatPath(lowerRelPath)
        try:
            theMeta = dropboxIndex[lowerRelPath]
        except:
            print '----------------------------------------'
            print 'File not found locally'
            return False
        upperRelPath = theMeta[1]
        upperRelPath = self.formatPath(upperRelPath)
        directory = self.formatPath(dropFileMan.dropboxLocalDirectory)
        fullPath = self.joinFilePath(directory, upperRelPath)
        if os.path.exists(fullPath):
            try:
                os.remove(fullPath)
            except:
                pass
        # If file not found now, return true
        if not os.path.exists(fullPath):
            return True
        # If file still exists, return false
        if os.path.exists(fullPath):
            return False

    def lookupLocal(self, relPath, localIndex):
        # Look for file in local index. If file exists return True,
        # otherwise False
        # Expects dict and upper or lower rel path. formatPath first.
        # Can be used for local dropbox index
        fileExists = False
        lowerPath = relPath.lower()
        for theFile, theMeta in localIndex.iteritems():
            if lowerPath == theFile:
                fileExists = True
        return fileExists

    def compareIndexDiffs(self, index1, index2):
        # Retuns a list of files on first index which are not on second index
        # Expects 2 dicts
        differenceList = {}
        inBoth = False
        for file1, meta1 in index1.iteritems():
            for file2, meta2 in index2.iteritems():
                if file1 == file2:
                    inBoth = True
                    break
            if inBoth is False:
                differenceList[file1] = meta1
            inBoth = False
        return differenceList

    def compareIndexSames(self, index1, index2):
        # Return dict of items in both index1 and index2
        # Expects 2 dicts
        simList = {}
        for file1, meta1 in index1.iteritems():
            for file2, meta2 in index2.iteritems():
                if file1 == file2:
                    simList[file1] = meta1
        return simList

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

    def compareTimes(self, commonItem, index1, index2):
        # Given an item known to be common to two indexes, compare
        # times and determine which index's time is newer
        # Return 1 for index1, 2 for index2 or 0 for same in both.
        # commonItem should be lowercase relpath
        for file1, meta1 in index1.iteritems():
            for file2, meta2 in index2.iteritems():
                if commonItem == file1:
                    if commonItem == file2:
                        # Check for empty metadata before popping
                        try:
                            time1 = meta1[0]
                            time2 = meta2[0]
                        except:
                            # Empty meta for one of the times, skip this check
                            break
                        if time1 > time2:
                            return 1
                        if time2 > time1:
                            return 2
                        else:
                            return 0

    def joinFilePath(self, directory, filePath):
        filePath = self.formatPath(filePath)
        directory = self.formatPath(directory)
        directory = '/' + directory
        fullPath = os.path.join(directory, filePath)
        return fullPath

    def localRemoteTimeCompare(self, remoteTime, lowerRelPath, localIndex):
        # Given the raw (not converted) time stamp from Dropbox,
        # compare to local index timestamp
        # Return True if remote is newer, False if local is
        # Assumes file is in local index
        # localIndex should be dict
        localMeta = localIndex[lowerRelPath]
        localTime = localMeta[0]
        remoteTime = self.convertTime(remoteTime)
        if localTime > remoteTime:
            return False
        if remoteTime > localTime:
            return True
        else:
            # Times are equal, so may aswel use local
            return False

    def convertTime(self, dropboxTime):
        # Convert dropbox time to local time
        utcLastModified = time.strptime(dropboxTime,
                                        '%a, %d %b %Y %H:%M:%S +0000')
        dropboxTime = calendar.timegm(utcLastModified)
        return dropboxTime
