import asyncio
import os
import re
import json

try:
    from urlparse import urlparse, parse_qs
    from urllib import urlencode, unquote
except ImportError:  # py 3.x
    from urllib.parse import urlparse, parse_qs, urlencode, unquote
import aiohttp


from pyxboxlive.gamerprofile import GamerProfile
from pyxboxlive.error import PyXboxLiveError
#from .exceptions import AuthenticationException, InvalidRequest

REQUESTS_TIMEOUT = 15



class XboxLiveClient(object):

    def __init__(self, username, password, timeout=REQUESTS_TIMEOUT, loop=None):
        """Initialize the client object."""
        self.username = username
        self.password = password

        if loop is None:
            loop = asyncio.get_event_loop()
        self._session = aiohttp.ClientSession(loop=loop)
        self._data = {}
        self._timeout = timeout
        self.authenticated = False

    @asyncio.coroutine
    def authenticate(self):
        '''Authenticated this client instance.'''
        if not self.username or not self.password:
            msg = (
                'Authentication credentials required. Please refer to '
                'http://xbox.readthedocs.org/en/latest/authentication.html'
            )
            raise PyXboxLiveError(msg)

        # firstly we have to GET the login page and extract
        # certain data we need to include in our POST request.
        # sadly the data is locked away in some javascript code
        base_url = 'https://login.live.com/oauth20_authorize.srf?'

        # if the query string is percent-encoded the server
        # complains that client_id is missing
        qs = unquote(urlencode({
            'client_id': '0000000048093EE3',
            'redirect_uri': 'https://login.live.com/oauth20_desktop.srf',
            'response_type': 'token',
            'display': 'touch',
            'scope': 'service::user.auth.xboxlive.com::MBI_SSL',
            'locale': 'en',
        }))
        resp = yield from self._session.get(base_url + qs)
        content = yield from resp.text()
        content = content.encode('utf-8')
        # python 3.x will error if this string is not a
        # bytes-like object
        url_re = b'urlPost:\\\'([A-Za-z0-9:\?_\-\.&/=]+)'
        ppft_re = b'sFTTag:\\\'.*value="(.*)"/>'

        login_post_url = re.search(url_re, content).group(1)
        post_data = {
            'login': self.username,
            'passwd': self.password,
            'PPFT': re.search(ppft_re, content).groups(1)[0].decode('utf-8'),
            'PPSX': 'Passpor',
            'SI': 'Sign in',
            'type': '11',
            'NewUser': '1',
            'LoginOptions': '1',
            'i3': '36728',
            'm1': '768',
            'm2': '1184',
            'm3': '0',
            'i12': '1',
            'i17': '0',
            'i18': '__Login_Host|1',
        }

        resp = yield from self._session.post(
            login_post_url.decode('utf-8'), data=post_data, allow_redirects=False,
        )

        if 'Location' not in resp.headers:
            # we can only assume the login failed
            msg = 'Could not log in with supplied credentials'
            raise PyXboxLiveError(msg)

        # the access token is included in fragment of the location header
        location = resp.headers['Location']
        parsed = urlparse(location)
        fragment = parse_qs(parsed.fragment)
        access_token = fragment['access_token'][0]

        url = 'https://user.auth.xboxlive.com/user/authenticate'
        resp = yield from self._session.post(url, data=json.dumps({
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType": "JWT",
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName": "user.auth.xboxlive.com",
                "RpsTicket": access_token,
            }
        }), headers={'Content-Type': 'application/json'})

        json_data = yield from resp.json()
        user_token = json_data['Token']
        uhs = json_data['DisplayClaims']['xui'][0]['uhs']

        url = 'https://xsts.auth.xboxlive.com/xsts/authorize'
        resp = yield from self._session.post(url, data=json.dumps({
            "RelyingParty": "http://xboxlive.com",
            "TokenType": "JWT",
            "Properties": {
                "UserTokens": [user_token],
                "SandboxId": "RETAIL",
            }
        }), headers={'Content-Type': 'application/json'})

        response = yield from resp.json()
        self.AUTHORIZATION_HEADER = 'XBL3.0 x=%s;%s' % (uhs, response['Token'])
        self.user_xid = response['DisplayClaims']['xui'][0]['xid']
        self.authenticated = True
        return self

    def close(self):
        """Close session"""
        self._session.close()

    def get_data(self):
        """Return collected data"""
        return self._data

    def __repr__(self):
        if self.authenticated:
            return '<xbox.Client: %s>' % self.username
        else:
            return '<xbox.Client: Unauthenticated>'

    @asyncio.coroutine
    def _get(self, url, **kw):
        '''
        Makes a GET request, setting Authorization
        header by default
        '''
        headers = kw.pop('headers', {})
        headers.setdefault('Content-Type', 'application/json')
        headers.setdefault('Accept', 'application/json')
        headers.setdefault('Authorization', self.AUTHORIZATION_HEADER)
        kw['headers'] = headers
        resp = yield from self._session.get(url, **kw)
#        self._raise_for_status(resp)
        return resp

    @asyncio.coroutine
    def get_gamerprofile_from_gamertag(self, gamertag):
        '''
        Instantiates an instance of ``GamerProfile`` from
        a gamertag

        :param gamertag: Gamertag to look up

        :raises: :class:`~xbox.exceptions.GamertagNotFound`

        :returns: :class:`~xbox.GamerProfile` instance
        '''
        url = 'https://profile.xboxlive.com/users/gt(%s)/profile/settings' % gamertag
        settings = [
            'AppDisplayName',
            'DisplayPic',
            'Gamerscore',
            'Gamertag',
            'PublicGamerpic',
            'XboxOneRep',
        ]

        qs = '?settings=%s' % ','.join(settings)
        headers = {'x-xbl-contract-version': '2'}

        resp = yield from self._get(url + qs, headers=headers)
        if resp.status == 404:
            raise GamertagNotFound('No such user')

        raw_json = yield from resp.json()
        user = raw_json['profileUsers'][0]
        return GamerProfile(self, user['id'], user['settings'], raw_json)

    def get_gamerprofile_from_xuid(self, xuid):
        '''
        Instantiates an instance of ``GamerProfile`` from
        an xuid

        :param xuid: Xuid to look up

        :raises: :class:`~xbox.exceptions.GamertagNotFound`

        :returns: :class:`~xbox.GamerProfile` instance
        '''

        url = 'https://profile.xboxlive.com/users/xuid(%s)/profile/settings' % xuid
        settings = [
            'AppDisplayName',
            'DisplayPic',
            'Gamerscore',
            'Gamertag',
            'PublicGamerpic',
            'XboxOneRep',
        ]

        qs = '?settings=%s' % ','.join(settings)
        headers = {'x-xbl-contract-version': '2'}

        resp = yield from self._get(url + qs, headers=headers)
        if resp.status == 404:
            raise GamertagNotFound('No such user: %s' % xuid)

        raw_json = yield from resp.json()
        user = raw_json['profileUsers'][0]
        return GamerProfile(self, user['id'], user['settings'], raw_json)


    @asyncio.coroutine
    def _post_json(self, url, data, **kw):
        '''
        Makes a POST request, setting Authorization
        and Content-Type headers by default
        '''
        data = json.dumps(data)
        headers = kw.pop('headers', {})
        headers.setdefault('Content-Type', 'application/json')
        headers.setdefault('Accept', 'application/json')

        kw['headers'] = headers
        kw['data'] = data
        response = yield from self._post(url, **kw)
        return response

    @asyncio.coroutine
    def _post(self, url, **kw):
        '''
        Makes a POST request, setting Authorization
        header by default
        '''
        headers = kw.pop('headers', {})
        headers.setdefault('Authorization', self.AUTHORIZATION_HEADER)
        kw['headers'] = headers
        resp = yield from self._session.post(url, **kw)
#        self._raise_for_status(resp)
        return resp


    @asyncio.coroutine
    def send_message(self, xuids, message):
        '''
        '''
        url = "https://msg.xboxlive.com/users/xuid(%s)/outbox" % self.user_xid

        recipients = [{"xuid": xuid} for xuid in xuids]
        data = {"header": {"recipients": recipients},
                "messageText": message,
               }
        headers = {'x-xbl-contract-version': '3'}
        response = yield from self._post_json(url, data, headers=headers)
        return response













#class Client(object):
#    '''
#    Base API client object handling authentication
#    and making requests.
#
#    A global instance of this is instantiated on import,
#    all you have to do is call the :meth:`~xbox.Client.authenticate`
#    method.
#
#    :var bool authenticated: whether client is authed
#
#    '''
#
#    def __init__(self):
#        self.session = requests.session()
#        self.authenticated = False
#
#    def _raise_for_status(self, response):
#        if response.status_code == 400:
#            try:
#                description = response.json()['description']
#            except:
#                description = 'Invalid request'
#            raise InvalidRequest(description, response=response)
#
#
#    def _post(self, url, **kw):
#        '''
#        Makes a POST request, setting Authorization
#        header by default
#        '''
#        headers = kw.pop('headers', {})
#        headers.setdefault('Authorization', self.AUTHORIZATION_HEADER)
#        kw['headers'] = headers
#        resp = self.session.post(url, **kw)
#        self._raise_for_status(resp)
#        return resp
#
#    def _post_json(self, url, data, **kw):
#        '''
#        Makes a POST request, setting Authorization
#        and Content-Type headers by default
#        '''
#        data = json.dumps(data)
#        headers = kw.pop('headers', {})
#        headers.setdefault('Content-Type', 'application/json')
#        headers.setdefault('Accept', 'application/json')
#
#        kw['headers'] = headers
#        kw['data'] = data
#        return self._post(url, **kw)
#
#    def __repr__(self):
#        if self.authenticated:
#            return '<xbox.Client: %s>' % self.login
#        else:
#            return '<xbox.Client: Unauthenticated>'
