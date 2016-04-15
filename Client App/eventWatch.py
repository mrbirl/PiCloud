import localFileMan
import watchdog.events as events


class watcher(events.FileSystemEventHandler):

    INDEX = 'localIndex.pickle'
    fileMan = None

    def __init__(self):
        print '----------------------------------------'
        print 'Started a path monitoring thread'
        watcher.fileMan = localFileMan.localFileMan()

    def on_moved(self, event):
        # Parameters: event(DirCreatedEvent or FileCreatedEvent)
        # Event representing file/directory creation.
        oldPath = str(event.src_path)
        newPath = str(event.dest_path)
        print '----------------------------------------'
        print 'File moved from ' + oldPath + ' to ' + newPath
        # Delete the original
        watcher.fileMan.removeFile(oldPath)
        # Add new
        watcher.fileMan.addFile(newPath)

    def on_created(self, event):
        # Parameters: event(DirCreatedEvent or FileCreatedEvent)
        # Event representing file/directory creation.
        path = str(event.src_path)
        print '----------------------------------------'
        print path + ' was created'
        # Add to the index
        watcher.fileMan.addFile(path)

    def on_deleted(self, event):
        # Parameters: event(DirCreatedEvent or FileCreatedEvent)
        # Event representing file/directory creation.
        path = str(event.src_path)
        print '----------------------------------------'
        print str(event.src_path) + ' was deleted'
        # Delete from index
        watcher.fileMan.removeFile(path)

    def on_modified(self, event):
        # Parameters: event(DirCreatedEvent or FileCreatedEvent)
        # Event representing file/directory creation.
        path = str(event.src_path)
        watcher.fileMan.addFile(path)
        print '----------------------------------------'
        print path + ' was modified'
