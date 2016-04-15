from dropbox import client, session
import webbrowser

# Authorise Dropbox - creates & returns Dropbox client object


def getClient():

    APP_KEY = 'theappkey'
    APP_SECRET = 'thesecret'
    ACCESS_TYPE = 'dropbox'

    try:
        # See if there is a text file with the tokens already
        TOKENS = 'dropbox_token.txt'
        token_file = open(TOKENS)
        token_key, token_secret = token_file.read().split('|')
        token_file.close()
        sess = session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
        sess.set_token(token_key, token_secret)
    except Exception:
        # Haven't authorised app already, so:
        # Creates a session
        sess = session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
        # requests a token using the session
        request_token = sess.obtain_request_token()
        # creates a athorisation-token using our session
        url = sess.build_authorize_url(request_token)
        # opens it in the browser
        webbrowser.open_new_tab(url)
        # when we're authorized, request a key-input
        print "Please authorize in the browser. After you're done, press enter."
        raw_input()
        # If we can obtain the access token, we're authenticated.
        access_token = sess.obtain_access_token(request_token)
        # Write these to a file for future reference...
        token_file = open(TOKENS, 'w')
        token_file.write("%s|%s" % (access_token.key, access_token.secret))
        token_file.close()

    # Initalizes the client so that we can do API-calls
    client = client.DropboxClient(sess)
    return client
