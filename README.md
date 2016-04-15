PiCloud
=======

My final year project - 
A home server application and corresponding client software which synchronises Dropbox, Google Drive and multiple folders on the client machine.

To run: 

- Install the Dropbox and Drive API's on a linux server
- Upload the server application files to the server
- Change paths in server application file to reflect paths on your server
- Add Dropbox and Drive app keys to Auth files

- Install PyCrypto on your client machine
- Change paths in main.py to the paths on your local machine you want to monitor
- Add your servers SFTP connection details to connectDriver.py

- Run server applications main.py
- Authenticate your Dropbox and Drive accounts when prompted
- Run client main.py

Enjoy!

Note: This was an early prototype and hasn't been updated in years - nothing catastrophic should happen, but nonetheless use at your own risk :)

There are now better ways to interact with the Dropbox and Drive APIs than what is done here, but this was what was available to me at the time.

All feedback welcome!
