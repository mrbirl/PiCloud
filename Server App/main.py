import os
import time
import dropDriver
import driveDriver
import clientSync
import execChanges

dropboxDriver = None
gdriveDriver = None

# All files are stored in this directory
backupDirectory = '/home/aUser/CloudDown/'
if not os.path.exists(backupDirectory):
    os.makedirs(backupDirectory, 0777)
    print '----------------------------------------'
    print 'Made Backup Directory'
print '----------------------------------------'
print 'Starting Dropbox...'
dropboxDriver = dropDriver.dropDriver(backupDirectory)
print '----------------------------------------'
print 'Starting Drive...'
gdriveDriver = driveDriver.driveDriver(backupDirectory)
print '----------------------------------------'
print '------ Changing Permissions ------'
for dirpath, dirnames, filenames in os.walk(backupDirectory):
    os.chmod(dirpath, 0777)
    for filename in filenames:
        fullPath = os.path.join(dirpath, filename)
        os.chmod(fullPath, 0777)
# Run inital sync
cliSync = clientSync.cSync(dropboxDriver.getRealIndex(),
                           gdriveDriver.getRealIndex())
changeRunner = execChanges.changeRunner()
# Service file managers
serviceFileMen = []
serviceFileMen.append(dropboxDriver.getFileMan())
serviceFileMen.append(gdriveDriver.getFileMan())
while 1:
    # Run Dropbox Delta
    dropboxDriver.checkRemote()
    # Run Drive Delta
    gdriveDriver.checkRemote()
    print '----------------------------------------'
    print '------ Changing Permissions ------'
    for dirpath, dirnames, filenames in os.walk(backupDirectory):
        os.chmod(dirpath, 0777)
        for filename in filenames:
            fullPath = os.path.join(dirpath, filename)
            os.chmod(fullPath, 0777)
    print '----------------------------------------'
    print '------ Checking Client ------'
    # Run Client Updates
    changeRunner.runClientUpdates()
    # Run Client Delta
    serviceUpDels = cliSync.delta()
    # Run client Updates
    changeRunner.runClientUpdates()
    # Run Service Updates
    serviceToUploads = serviceUpDels[0]
    serviceToDeletes = serviceUpDels[1]
    changeRunner.bulkServiceUpdate(serviceToUploads,
                                   dropboxDriver.getRealIndex(),
                                   gdriveDriver.getRealIndex())
    changeRunner.runServiceDeletes(serviceToDeletes, serviceFileMen)
    # Take a break
    time.sleep(2)
