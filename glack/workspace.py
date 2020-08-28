from gi.repository import Gio, GObject

from glack.emoji_loader import EmojiLoader
from glack.rtm_handler import RtmHandler
from glack.slack import SlackRtmClient, SlackWebClient

from glack.models.channel import Channel
from glack.models.emoji import Emoji
from glack.models.user import User


class Workspace(GObject.GObject):
    __gsignals__ = {
        'channel-added': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'emoji-added': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'started': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'user-added': (GObject.SignalFlags.RUN_FIRST, None, (object,))
    }

    channels = Gio.ListStore()
    _channels_by_id = {}

    current_team = None

    current_user = None

    emoji_loader = EmojiLoader()

    emojis = Gio.ListStore()

    rtm = SlackRtmClient()

    users = Gio.ListStore()
    _users_by_id = {}

    web = SlackWebClient()

    def __init__(self):
        GObject.GObject.__init__(self)
        self.rtm_handler = RtmHandler(self)
        self._load_emojis()

    def get_channel(self, channel_id):
        return self._channels_by_id[channel_id]

    def get_user(self, user_id):
        return self._users_by_id[user_id]

    def has_channel(self, channel_id):
        return channel_id in self._channels_by_id

    def has_user(self, user_id):
        return user_id in self._users_by_id

    def start(self):
        self.rtm.run(self._on_rtm_start, self._on_rtm_message)
        self.web.emoji_list({}, self._on_emoji_list)

    def _add_channel(self, data):
        channel = Channel.new_from_data(self, data)
        self._channels_by_id[channel.id] = channel
        self.channels.append(channel)
        self.emit('channel-added', channel)

    def _load_emojis(self):
        emojis = []
        for name, path in self.emoji_loader.emoji.items():
            emoji = Emoji(name, path)
            emojis.append(emoji)
            self.emit('emoji-added', emoji)
        self.emojis.splice(len(self.emojis), 0, emojis)

    def _on_emoji_list(self, data):
        def on_loaded(name, path):
            emoji = Emoji(name, path)
            self.emojis.append(emoji)
            self.emit('emoji-added', emoji)
        for k, v in data['emoji'].items():
            if not v.startswith('alias:'):
                self.emoji_loader.add_custom(k, v, on_loaded)

    def _on_rtm_message(self, message):
        self.rtm_handler.handle(message)

    def _on_rtm_start(self, start_response):
        self.current_team = start_response['team']

        self.current_user = start_response['self']

        self._set_users(start_response['users'])

        channels = []
        for channel_kind in ['channels', 'groups', 'ims', 'mpims']:
            channels.extend(start_response[channel_kind])
        self._set_channels(channels)

        self.rtm.presence_sub([u.id for u in self.users])

        self.emit('started')

    def _set_channels(self, data):
        channels = []
        for channel_data in data:
            channel = Channel.new_from_data(self, channel_data)
            self._channels_by_id[channel.id] = channel
            channels.append(channel)
            self.emit('channel-added', channel)
        self.channels.splice(0, len(self.channels), channels)

    def _set_users(self, data):
        users = []
        for user_data in data:
            user = User(self, user_data)
            self._users_by_id[user.id] = user
            users.append(user)
            self.emit('user-added', user)
        self.users.splice(0, len(self.users), users)
