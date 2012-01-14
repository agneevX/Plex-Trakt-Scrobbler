import logsucker
import hashlib

APPLICATIONS_PREFIX = "/applications/trakttv"

NAME = L('Title')

# make sure to replace artwork with what you want
# these filenames reference the example files in
# the Contents/Resources/ folder in the bundle
ART  = 'art-default.jpg'
ICON = 'icon-default.png'
PMS_URL = 'http://%s/library/sections/'
TRAKT_URL = 'http://api.trakt.tv/%s/ba5aa61249c02dc5406232da20f6e768f3c82b28'

responses = {
    100: ('Continue', 'Request received, please continue'),
    101: ('Switching Protocols',
          'Switching to new protocol; obey Upgrade header'),

    200: ('OK', 'Request fulfilled, document follows'),
    201: ('Created', 'Document created, URL follows'),
    202: ('Accepted',
          'Request accepted, processing continues off-line'),
    203: ('Non-Authoritative Information', 'Request fulfilled from cache'),
    204: ('No Content', 'Request fulfilled, nothing follows'),
    205: ('Reset Content', 'Clear input form for further input.'),
    206: ('Partial Content', 'Partial content follows.'),

    300: ('Multiple Choices',
          'Object has several resources -- see URI list'),
    301: ('Moved Permanently', 'Object moved permanently -- see URI list'),
    302: ('Found', 'Object moved temporarily -- see URI list'),
    303: ('See Other', 'Object moved -- see Method and URL list'),
    304: ('Not Modified',
          'Document has not changed since given time'),
    305: ('Use Proxy',
          'You must use proxy specified in Location to access this '
          'resource.'),
    307: ('Temporary Redirect',
          'Object moved temporarily -- see URI list'),

    400: ('Bad Request',
          'Bad request syntax or unsupported method'),
    401: ('Unauthorized',
          'Login failed'),
    402: ('Payment Required',
          'No payment -- see charging schemes'),
    403: ('Forbidden',
          'Request forbidden -- authorization will not help'),
    404: ('Not Found', 'Nothing matches the given URI'),
    405: ('Method Not Allowed',
          'Specified method is invalid for this server.'),
    406: ('Not Acceptable', 'URI not available in preferred format.'),
    407: ('Proxy Authentication Required', 'You must authenticate with '
          'this proxy before proceeding.'),
    408: ('Request Timeout', 'Request timed out; try again later.'),
    409: ('Conflict', 'Request conflict.'),
    410: ('Gone',
          'URI no longer exists and has been permanently removed.'),
    411: ('Length Required', 'Client must specify Content-Length.'),
    412: ('Precondition Failed', 'Precondition in headers is false.'),
    413: ('Request Entity Too Large', 'Entity is too large.'),
    414: ('Request-URI Too Long', 'URI is too long.'),
    415: ('Unsupported Media Type', 'Entity body in unsupported format.'),
    416: ('Requested Range Not Satisfiable',
          'Cannot satisfy request range.'),
    417: ('Expectation Failed',
          'Expect condition could not be satisfied.'),

    500: ('Internal Server Error', 'Server got itself in trouble'),
    501: ('Not Implemented',
          'Server does not support this operation'),
    502: ('Bad Gateway', 'Invalid responses from another server/proxy.'),
    503: ('Service Unavailable',
          'The server cannot process the request due to a high load'),
    504: ('Gateway Timeout',
          'The gateway server did not receive a timely response'),
    505: ('HTTP Version Not Supported', 'Cannot fulfill request.'),
    }

####################################################################################################

def Start():

    ## make this plugin show up in the 'Applications' section
    ## in Plex. The L() function pulls the string out of the strings
    ## file in the Contents/Strings/ folder in the bundle
    ## see also:
    ##  http://dev.plexapp.com/docs/mod_Plugin.html
    ##  http://dev.plexapp.com/docs/Bundle.html#the-strings-directory
    Plugin.AddPrefixHandler(APPLICATIONS_PREFIX, ApplicationsMainMenu, NAME, ICON, ART)

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    ## set some defaults so that you don't have to
    ## pass these parameters to these object types
    ## every single time
    ## see also:
    ##  http://dev.plexapp.com/docs/Objects.html
    MediaContainer.title1 = NAME
    MediaContainer.viewGroup = "List"
    MediaContainer.art = R(ART)
    DirectoryItem.thumb = R(ICON)
    VideoItem.thumb = R(ICON)

def ValidatePrefs():
    u = Prefs['username']
    p = Prefs['password']
    ## do some checks and return a
    ## message container
    

    status = talk_to_trakt('account/test', {'username' : u, 'password' : hashlib.sha1(p).hexdigest()})
    if status['status']:
        return MessageContainer(
            "Success",
            "Trakt responded with: %s " % status['message']
        )
    else:
        return MessageContainer(
            "Error",
            "Trakt responded with: %s " % status['message']
        )

def ApplicationsMainMenu():

    dir = MediaContainer(viewGroup="InfoList", noCache=True)
    dir.Append(
        Function(
            DirectoryItem(
                ManuallySync,
                "Manually Sync to trakt.tv",
                summary="Sync current library to trakt.tv",
                thumb=R(ICON),
                art=R(ART)
            )
        )
    )  
    dir.Append(
        PrefsItem(
            title="Trakt.tv preferences",
            subtile="Configure your trakt.tv account",
            summary="Configure how to connect to trakt.tv",
            thumb=R(ICON)
        )
    )

    # ... and then return the container
    return dir

def ManuallySync(sender):
    title = "Dummy"
    key = "1"
    

    url = GetPmsHost() + key + '/refresh'
    update = HTTP.Request(url, cacheTime=1).content

    if title == 'All sections':
        return MessageContainer(title, 'All sections will be updated!')
    elif len(key) > 1:
        return MessageContainer(title, 'All chosen sections will be updated!')
    else:
        return MessageContainer(title, 'Section "' + title + '" will be updated!')

def GetPmsHost():
  host = Prefs['pms_host']

  if host.find(':') == -1:
    host += ':32400'

  return PMS_URL % (host)

def talk_to_trakt(action, values):
    # Function to talk to the trakt.tv api
    data_url = TRAKT_URL % action

    try:
        json_file = HTTP.Request(data_url, values=values)
        headers = json_file.headers
        result = JSON.ObjectFromString(json_file.content)
        Log(result)

    except Ex.HTTPError, e:
        result = {'status' : 'failure', 'error' : responses[e.code][1]}

    if result['status'] == 'success':
        Log('Trakt responded with: %s' % result['message'])
        return {'status' : True, 'message' : result['message']}
    else:
        Log('Trakt responded with: %s' % result['error'])
        return {'status' : False, 'message' : result['error']}