from gi.repository import Gio, GObject

from glack.models import message
from glack.models.user import User


class Channel(GObject.GObject):
    id = GObject.Property(type=str)
    is_open = GObject.Property(type=bool, default=False)
    last_read = GObject.Property(type=str)
    latest = GObject.Property(type=str)
    name = GObject.Property(type=str)
    topic = GObject.Property(type=str)

    _member_ids = None

    @GObject.Property(type=GObject.TYPE_STRV)
    def member_ids(self):
        return self._member_ids

    members = None
    messages = None

    def __init__(self, ws, data):
        super().__init__()

        self._ws = ws

        self.id = data['id']

        self.members = Gio.ListStore()

        self.messages = Gio.ListStore()
        self._messages_by_ts = {}

        if 'last_read' in data:
            self.last_read = data['last_read']
        if 'members' in data:
            self.member_ids = data['members']
        if 'topic' in data:
            self.topic = data['topic']['value']

    @staticmethod
    def new_from_data(ws, data):
        if 'is_channel' in data and data['is_channel']:
            return PublicChannel(ws, data)
        elif 'is_mpim' in data and data['is_mpim']:
            return MpimChannel(ws, data)
        elif 'is_group' in data and data['is_group']:
            return PrivateChannel(ws, data)
        elif 'is_im' in data and data['is_im']:
            return ImChannel(ws, data)

    @member_ids.setter
    def member_ids(self, value):
        self._member_ids = value

        self.members.splice(
            0,
            len(self.members),
            [
                self._ws.get_user(member_id)
                for member_id in self._member_ids
            ]
        )

        self.members.sort(self._members_sort_func)

    def add_member(self, member):
        self.members.insert_sorted(member, self._members_sort_func)

    def add_message(self, message):
        self.messages.insert_sorted(message, self._messages_sort_func)
        self._messages_by_ts[message.ts] = message
        if not self.latest or message.ts > self.latest:
            self.latest = message.ts

    def get_message(self, ts):
        return self._messages_by_ts[ts]

    def has_message(self, ts):
        return ts in self._messages_by_ts

    def load_history(self):
        def finish(data):
            for message_data in data['messages']:
                self.add_message(message.Message(self._ws, self, message_data))
        self._ws.web.conversations_history({'channel': self.id}, finish)

    def post_message(self, text):
        self._ws.web.chat_post_message({
            'channel': self.id,
            'text': text
        })

    def remove_member(self, member):
        index = next(
            i for i, m in enumerate(self.members)
            if m == member
        )
        self.members.remove(index)

    @staticmethod
    def _members_sort_func(a, b):
        aname = a.name.lower()
        bname = b.name.lower()
        if aname == bname:
            return 0
        else:
            return 1 if aname > bname else -1

    @staticmethod
    def _messages_sort_func(a, b):
        if a.ts == b.ts:
            return 0
        else:
            return 1 if a.ts > b.ts else -1


class PublicChannel(Channel):
    def __init__(self, ws, data):
        super().__init__(ws, data)
        self.is_open = 'is_member' in data and data['is_member']
        self.name = data['name']

    def leave(self):
        self._ws.web.channels_leave({'channel': self.id})

    def load_latest(self):
        def finish(data):
            if 'latest' in data['channel']:
                self.latest = data['channel']['latest']['ts']
        self._ws.web.channels_info({'channel': self.id}, finish)

    def mark_read(self):
        self._ws.web.channels_mark({
            'channel': self.id,
            'ts': self.latest
        })


class PrivateChannel(Channel):
    def __init__(self, ws, data):
        super().__init__(ws, data)
        self.is_open = 'is_open' in data and data['is_open']
        self.name = data['name']

    def leave(self):
        self._ws.web.groups_leave({'channel': self.id})

    def load_latest(self):
        def finish(data):
            if 'latest' in data['group']:
                self.latest = data['group']['latest']['ts']
        self._ws.web.groups_info({'channel': self.id}, finish)

    def mark_read(self):
        self._ws.web.groups_mark({
            'channel': self.id,
            'ts': self.latest
        })


class ImChannel(Channel):
    user_id = GObject.Property(type=str)
    user = GObject.Property(type=User)

    def __init__(self, ws, data):
        super().__init__(ws, data)

        self.user_id = data['user']
        self.user = ws.get_user(self.user_id)

        self.is_open = 'is_open' in data and data['is_open']
        self.member_ids = [ws.current_user['id'], data['user']]
        self.name = self.user.name

    def close(self):
        self._ws.web.im_close({'channel': self.id})

    def load_latest(self):
        def finish(data):
            if data['messages']:
                self.latest = data['messages'][0]['ts']
        self._ws.web.conversations_history({
            'channel': self.id,
            'count': '1'
        }, finish)

    def mark_read(self):
        self._ws.web.im_mark({
            'channel': self.id,
            'ts': self.latest
        })


class MpimChannel(Channel):
    def __init__(self, ws, data):
        super().__init__(ws, data)

        self.is_open = 'is_open' in data and data['is_open']

        self.name = ', '.join([
            member.name
            for member in self.members
            if member.id != self._ws.current_user['id']
        ])

    def close(self):
        self._ws.web.mpim_close({'channel': self.id})

    def load_latest(self):
        def finish(data):
            if data['messages']:
                self.latest = data['messages'][0]['ts']
        self._ws.web.conversations_history({
            'channel': self.id,
            'count': '1'
        }, finish)

    def mark_read(self):
        self._ws.web.mpim_mark({
            'channel': self.id,
            'ts': self.latest
        })
