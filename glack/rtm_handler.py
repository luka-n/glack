from glack.models.message import Message


class RtmHandler:
    def __init__(self, ws):
        self.ws = ws

    def handle(self, data):
        if 'subtype' in data:
            handler_name = 'on_{}_{}'.format(
                data['type'],
                data['subtype']
            )
        else:
            handler_name = 'on_{}'.format(data['type'])
        if hasattr(self, handler_name):
            handler = getattr(self, handler_name)
            if callable(handler):
                handler(data)

    def on_channel_joined(self, data):
        channel = self.ws.get_channel(data['channel']['id'])
        channel.is_open = True

    def on_channel_left(self, data):
        channel = self.ws.get_channel(data['channel'])
        channel.is_open = False

    def on_channel_marked(self, data):
        channel = self.ws.get_channel(data['channel'])
        channel.last_read = data['ts']

    def on_group_joined(self, data):
        if not data['channel']['is_mpim']:
            self.ws._add_channel(data['channel'])

    def on_group_left(self, data):
        channel = self.ws.get_channel(data['channel'])
        channel.is_open = False

    def on_group_marked(self, data):
        channel = self.ws.get_channel(data['channel'])
        channel.last_read = data['ts']

    def on_im_close(self, data):
        channel = self.ws.get_channel(data['channel'])
        channel.is_open = False

    def on_im_joined(self, data):
        self.ws._add_channel(data['channel'])

    def on_im_marked(self, data):
        channel = self.ws.get_channel(data['channel'])
        channel.last_read = data['ts']

    def on_im_open(self, data):
        channel = self.ws.get_channel(data['channel'])
        channel.is_open = True

    def on_member_joined_channel(self, data):
        channel = self.ws.get_channel(data['channel'])
        user = self.ws.get_user(data['user'])
        channel.add_member(user)

    def on_member_left_channel(self, data):
        channel = self.ws.get_channel(data['channel'])
        user = self.ws.get_user(data['user'])
        channel.remove_member(user)

    def on_message(self, data):
        hidden = 'hidden' not in data or not data['hidden']
        if hidden:
            channel = self.ws.get_channel(data['channel'])
            message = Message(self.ws, channel, data)
            channel.add_message(message)

    def on_message_message_changed(self, data):
        channel = self.ws.get_channel(data['channel'])
        if channel.has_message(data['message']['ts']):
            message = channel.get_message(data['message']['ts'])
            message.set_from_data(data['message'])

    def on_mpim_close(self, data):
        channel = self.ws.get_channel(data['channel'])
        channel.is_open = False

    def on_mpim_joined(self, data):
        self.ws._add_channel(data['channel'])

    def on_mpim_marked(self, data):
        channel = self.ws.get_channel(data['channel'])
        channel.last_read = data['ts']

    def on_mpim_open(self, data):
        channel = self.ws.get_channel(data['channel'])
        channel.is_open = True

    def on_presence_change(self, data):
        user = self.ws.get_user(data['user'])
        user.presence = data['presence']

    def on_user_change(self, data):
        user = self.ws.get_user(data['user']['id'])
        user.set_from_data(data['user'])
