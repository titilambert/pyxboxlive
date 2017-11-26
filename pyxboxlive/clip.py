class Clip(object):
    '''
    Represents a single game clip.

    :var user: User that made the clip
    :var string clip_id: Unique id of the clip
    :var string scid: Unique SCID of the clip
    :var string duration: Duration, in seconds, of the clip
    :var string name: Name of the clip. Can be ``''``
    :var bool saved: Whether the user has saved the clip.
        Clips that aren't saved eventually expire
    :var string state:
    :var string views: Number of views the clip has had
    :var string rating: Clip rating
    :var string ratings: Number of ratings the clip has received
    :var string caption: User-defined clip caption
    :var dict thumbnails: Thumbnail URLs for the clip
    :var datetime recorded: Date and time clip was made
    :var string media_url: Video clip URL
    '''

    def __init__(self, user, clip_data):
        self.raw_json = clip_data
        self.user = user
        self.clip_id = clip_data['gameClipId']
        self.scid = clip_data['scid']
        self.duration = clip_data['durationInSeconds']
        self.name = clip_data['clipName']
        self.saved = clip_data['savedByUser']
        self.state = clip_data['state']
        self.views = clip_data['views']
        self.rating = clip_data['rating']
        self.ratings = clip_data['ratingCount']
        self.caption = clip_data['userCaption']
        self.thumbnails = DotNotationDict()
        self.recorded = datetime.strptime(
            clip_data['dateRecorded'], '%Y-%m-%dT%H:%M:%SZ'
        )

        # thumbnails and media_url may not yet exist
        # if the state of the clip is PendingUpload
        self.thumbnails.small = None
        self.thumbnails.large = None
        for thumb in clip_data['thumbnails']:
            if thumb['thumbnailType'] == 'Small':
                self.thumbnails.small = thumb['uri']
            elif thumb['thumbnailType'] == 'Large':
                self.thumbnails.large = thumb['uri']

        self.media_url = None
        for uri in clip_data['gameClipUris']:
            if uri['uriType'] == 'Download':
                self.media_url = uri['uri']

    def __getstate__(self):
        return (self.raw_json, self.user)

    def __setstate__(self, data):
        clip_data = data[0]
        user = data[1]
        self.__init__(user, clip_data)

    @classmethod
    @authenticates
    def get(cls, client, xuid, scid, clip_id):
        '''
        Gets a specific game clip

        :param xuid: xuid of an xbox live user
        :param scid: scid of a clip
        :param clip_id: id of a clip
        '''
        url = (
            'https://gameclipsmetadata.xboxlive.com/users'
            '/xuid(%(xuid)s)/scids/%(scid)s/clips/%(clip_id)s' % {
                'xuid': xuid,
                'scid': scid,
                'clip_id': clip_id,
            }
        )
        resp = client._get(url)

        # scid does not seem to matter when fetching clips,
        # as long as it looks like a uuid it should be fine.
        # perhaps we'll raise an exception in future
        if resp.status_code == 404:
            msg = 'Could not find clip: xuid=%s, scid=%s, clip_id=%s' % (
                xuid, scid, clip_id,
            )
            raise ClipNotFound(msg)

        data = resp.json()

        # as we don't have the user object let's
        # create a lazily evaluated proxy object
        # that will fetch it only when required
        user = UserProxy(xuid)
        return cls(user, data['gameClip'])

    @classmethod
    @authenticates
    def saved_from_user(cls, client, user, include_pending=False):
        '''
        Gets all clips 'saved' by a user.

        :param user: :class:`~xbox.GamerProfile` instance
        :param bool include_pending: whether to ignore clips that are not
            yet uploaded. These clips will have thumbnails and media_url
            set to ``None``
        :returns: Iterator of :class:`~xbox.Clip` instances
        '''

        url = 'https://gameclipsmetadata.xboxlive.com/users/xuid(%s)/clips/saved'
        resp = client._get(url % user.xuid)
        data = resp.json()
        for clip in data['gameClips']:
            if clip['state'] != 'PendingUpload' or include_pending:
                yield cls(user, clip)

    @classmethod
    @authenticates
    def latest_from_user(cls, client, user, include_pending=False):
        '''
        Gets all clips, saved and unsaved

        :param user: :class:`~xbox.GamerProfile` instance
        :param bool include_pending: whether to ignore clips that are not
            yet uploaded. These clips will have thumbnails and media_url
            set to ``None``

        :returns: Iterator of :class:`~xbox.Clip` instances
        '''

        url = 'https://gameclipsmetadata.xboxlive.com/users/xuid(%s)/clips'
        resp = client._get(url % user.xuid)
        data = resp.json()
        for clip in data['gameClips']:
            if clip['state'] != 'PendingUpload' or include_pending:
                yield cls(user, clip)
