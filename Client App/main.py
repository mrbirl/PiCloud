import sys
import os
import time
import localIndex
import clientLocalCheck
import connectDriver


paths = {}  # The paths to monitor

# Path to which miscellaneous Dropbox files will be downloaded
defaultDropPath = '/Users/aUser/Downloads/Misc Dropbox Files/'
defaultDropDestination = 'dropbox'
paths[defaultDropPath] = defaultDropDestination
# Path to which miscellaneous Drive files will be downloaded
defaultDrivePath = '/Users/aUser/Downloads/Misc Drive Files'
defaultDriveDestination = 'drive'
paths[defaultDrivePath] = defaultDriveDestination

path1 = '/Users/aUser/Documents/Photos/'
destination1 = 'dropbox'
paths[path1] = destination1
path2 = '/Users/aUser/Music/'
destination2 = 'drive'
paths[path2] = destination2
path3 = '/Users/aUser/Documents/'
destination3 = 'dropdrive'
paths[path3] = destination3

# Create the miscellaneous download locations if they don't exist already
if not os.path.exists(defaultDropPath):
    os.makedirs(defaultDropPath)
if not os.path.exists(defaultDrivePath):
    os.makedirs(defaultDrivePath)

localIndex = localIndex.localIndex(paths)
localIndex.printIndex()

# Start local file check threads
serverConnect = connectDriver.cDriver()
threadManager = clientLocalCheck.localCheck(paths)
serverConnect.connect()  # Start connection
try:
    while True:
        # Run server connection work, then wait 10 seconds
        serverConnect.run()
        time.sleep(10)
except (KeyboardInterrupt, SystemExit):
    serverConnect.close()  # End sftp connection
    sys.exit()
