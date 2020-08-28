from gi.repository import GObject


class Emoji(GObject.GObject):
    name = GObject.Property(type=str)
    path = GObject.Property(type=str)

    def __init__(self, name, path):
        super().__init__()

        self.name = name
        self.path = path
