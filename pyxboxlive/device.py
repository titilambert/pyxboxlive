import dateutil.parser


class Device():

    def __init__(self, type_, titles):
        self.type_ = type_
        self.titles = titles

    def __repr__(self):
        return '<pyxbox.device.Device: {}>'.format(self.type_)


class Title():
    def __init__(self, id, name, placement, state, lastModified):
        self.id_ = id
        self.name = name
        self.placement = placement
        self.state = state
        try:
            self.last_modified = dateutil.parser.parse(lastModified)
        except ValueError:
            self.last_modified = None

    def __repr__(self):
        return '<pyxbox.device.Title: {} ({}, {})>'.format(self.name, self.state, self.placement)
