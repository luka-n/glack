from gi.repository import GObject

from glack.models import channel
from glack.models.user import User


class Message(GObject.GObject):
    channel = GObject.Property(type=channel.Channel)
    channel_id = GObject.Property(type=str)
    text = GObject.Property(type=str)
    ts = GObject.Property(type=str)
    user = GObject.Property(type=User)
    user_id = GObject.Property(type=str)

    def __init__(self, ws, channel, data):
        super().__init__()

        self._ws = ws

        self.channel_id = channel.id
        self.ts = data['ts']
        self.user_id = data['user']

        self.channel = channel
        self.user = self._ws.get_user(self.user_id)

        self.set_from_data(data)

    def set_from_data(self, data):
        if data['text'] != self.text:
            self.text = data['text']
