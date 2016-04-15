import os
import pickle
import localFileMan


class localIndex:

    theIndex = {}
    oldIndex = {}
    differneces = {}
    fileMan = None

    INDEX = 'localIndex.pickle'
    MONITORED = 'monitoredPaths.pickle'
    monitoredPaths = []

    def __init__(self, paths):
        # build a dictionary of type {lowPath = [lastModified, casePath, baseLocation, destination]}
        # baseLocation is the root directory being monitored.
        # This maps to root of dropbox or drive
        # lowPath and casePath are relative to the baseLocation
        localIndex.fileMan = localFileMan.localFileMan()
        localIndex.fileMan.picklePaths(paths)
        self.build(paths)

    def build(self, paths):
        print '----------------------------------------'
        print 'Building local index'
        # Overwrite any old index
        with open(localIndex.INDEX, 'wb') as the_index:
            pickle.dump(localIndex.theIndex, the_index)
        for path, destination in paths.iteritems():
            baseLocation = path
            # Keep a list of monitored locations
            localIndex.monitoredPaths.append(baseLocation)
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    if not os.path.isdir(filename):
                        fullPath = os.path.join(dirpath, filename)
                        localIndex.fileMan.addFile(fullPath)

    def pickleIndex(self):
        # Save the index, just another way to call the localFileMan function
        localIndex.fileMan.pickleIndex(localIndex.theIndex)

    def getIndex(self):
        self.refresh()
        return localIndex.theIndex

    def addFile(self, fullPath):
        # Add a file to the index, another way of calling localFileMan's method
        localIndex.fileMan.addFile(fullPath)

    def removeFile(self, fullPath):
        # Remove a file to the index, another way to call localFileMan method
        localIndex.fileMan.removeFile(fullPath)

    def addMonitor(self, path):
        # add a path being monitored to the monitored list
        self.monitoredPaths.append(path)

    def printIndex(self):
        self.refresh()
        print localIndex.theIndex

    def refresh(self):
        localIndex.theIndex = localIndex.fileMan.loadIndex()
