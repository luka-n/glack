from gi.repository import GObject


class Avatar(GObject.GObject):
    avatar_hash = GObject.Property(type=str)
    avatar_url = GObject.Property(type=str)

    def __init__(self, avatar_hash, avatar_url):
        super().__init__()

        self.avatar_hash = avatar_hash
        self.avatar_url = avatar_url

    def __eq__(self, obj):
        return isinstance(obj, Avatar) and \
            obj.avatar_hash == self.avatar_hash

    def __ne__(self, obj):
        return not self == obj
