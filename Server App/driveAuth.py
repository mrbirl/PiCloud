import pickle
import time
import httplib2
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
# Authorises Drive, creates and returns drive service object


def getClient():

    CLIENT_ID = 'theid'
    CLIENT_SECRET = 'thesecret'
    # Check https://developers.google.com/drive/scopes for all available scopes
    OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'
    # Redirect URI for installed apps
    REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
    # Where to save the creds
    CREDENTIALS = 'driveCredentials.pickle'

    try:
        with open(CREDENTIALS, 'r') as the_creds:
            credentials = pickle.load(the_creds)
    except:
        # Run through the OAuth flow and retrieve credentials
        flow = OAuth2WebServerFlow(CLIENT_ID,
                                   CLIENT_SECRET,
                                   OAUTH_SCOPE,
                                   REDIRECT_URI)
        authorize_url = flow.step1_get_authorize_url()
        print 'Go to the following link in your browser: ' + authorize_url
        code = raw_input('Enter verification code: ').strip()
        credentials = flow.step2_exchange(code)
        with open(CREDENTIALS, 'w') as the_creds:
            pickle.dump(credentials, the_creds)

    # Create an httplib2.Http object and authorize it with our credentials
    http = httplib2.Http()
    http = credentials.authorize(http)
    callFailed = True
    while callFailed is True:
        try:
            print 'Authenticating Drive...'
            drive_service = build('drive', 'v2', http=http)
            callFailed = False
            print 'Successfully authenticated'
        except:
            print 'Drive auth call failed, going to try again'
            time.sleep(1)
    return drive_service
