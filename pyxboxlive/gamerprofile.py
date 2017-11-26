import asyncio

STATE_UNKNOWN = "unknown"

from pyxboxlive.device import Device, Title

class GamerProfile(object):
    '''
    Represents an xbox live user.

    :var string xuid: xuid of user
    :var string gamertag: gamertag of user
    :var string gamerscore: gamerscore of user
    :var string gamerpic: url for gamerpic of user
    '''

    def __init__(self, client, xuid, settings, user_data):
        self.xuid = xuid
        self._client = client
        self.raw_json = user_data
        self.state = None
        self.devices = []
        name_map = {
            'Gamertag': 'gamertag',
            'Gamerscore': 'gamerscore',
            'PublicGamerpic': 'gamerpic',
        }
        for setting in settings:
            if setting['id'] in name_map:
                setattr(self, name_map[setting['id']], setting['value'])

    @classmethod
    def from_xuid(cls, client, xuid):
        '''
        Instantiates an instance of ``GamerProfile`` from
        an xuid

        :param xuid: Xuid to look up

        :raises: :class:`~xbox.exceptions.GamertagNotFound`

        :returns: :class:`~xbox.GamerProfile` instance
        '''

        url = 'https://profile.xboxlive.com/users/xuid(%s)/profile/settings' % xuid
        try:
            return cls._fetch(client, url)
        except (GamertagNotFound, InvalidRequest):
            # this endpoint seems to return 400 when the resource
            # does not exist
            raise GamertagNotFound('No such user: %s' % xuid)

    @classmethod
    @asyncio.coroutine
    def from_gamertag(cls, client, gamertag):
        '''
        Instantiates an instance of ``GamerProfile`` from
        a gamertag

        :param gamertag: Gamertag to look up

        :raises: :class:`~xbox.exceptions.GamertagNotFound`

        :returns: :class:`~xbox.GamerProfile` instance
        '''
        url = 'https://profile.xboxlive.com/users/gt(%s)/profile/settings' % gamertag
        try:
            ret = yield from  cls._fetch(client, url)
            return ret
        except Exception:
            raise Exception('No such user: %s' % gamertag)

    @classmethod
    @asyncio.coroutine
    def _fetch(cls, client, base_url):
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

        resp = yield from client._get(base_url + qs, headers=headers)
        if resp.status == 404:
            raise GamertagNotFound('No such user')

        raw_json = yield from resp.json()
        user = raw_json['profileUsers'][0]
        return cls(client, user['id'], user['settings'], raw_json)

    @asyncio.coroutine
    def update_devices(self):
        '''
        '''
        url = "https://userpresence.xboxlive.com/users/batch"
        data = {"users": [self.xuid], "level": "all"}
        headers = {
            'x-xbl-contract-version': '2',
            'User-Agent': ('XboxRecord.Us Like SmartGlass/2.105.0415 '
                           'CFNetwork/711.3.18 Darwin/14.0.0')}
        response = yield from self._client._post_json(url, data=data,
                                                      headers=headers)

        if response.status != 200:
            _LOGGER.error("Can not get %s presence", self._gamertag)
            return
        results = yield from response.json()
        if len(results) != 1:
            _LOGGER.error("Can not get %s presence", self._gamertag)
            return

        # Save state
        self.state = results[0].get('state', STATE_UNKNOWN).lower()
        # Save devices
        self.devices = []
        devices = results[0].get('devices', [])
        for device in devices:
            titles = []
            for title in device.get('titles', []):
                titles.append(Title(**title))
            dev = Device(device['type'], titles)
            self.devices.append(dev)

    def __repr__(self):
        return '<pyxbox.gamerprofile.GamerProfile: {} ({})>'.format(self.gamertag, self.xuid)
