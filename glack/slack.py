import json
import os

from gi.repository import Soup


class SlackWebClient:
    def __init__(self):
        self._soup = Soup.SessionAsync()
        self._token = os.environ['GLACK_TOKEN']

    def channels_info(self, params={}, callback=None):
        self._request(
            'GET',
            'https://slack.com/api/channels.info',
            {'token': self._token, **params},
            callback
        )

    def channels_join(self, params={}, callback=None):
        self._request(
            'POST',
            'https://slack.com/api/channels.join',
            {'token': self._token, **params},
            callback
        )

    def channels_leave(self, params={}, callback=None):
        self._request(
            'POST',
            'https://slack.com/api/channels.leave',
            {'token': self._token, **params},
            callback
        )

    def channels_mark(self, params={}, callback=None):
        self._request(
            'POST',
            'https://slack.com/api/channels.mark',
            {'token': self._token, **params},
            callback
        )

    def chat_post_message(self, params={}, callback=None):
        self._request(
            'POST',
            'https://slack.com/api/chat.postMessage',
            {'as_user': 'true', 'token': self._token, **params},
            callback
        )

    def conversations_history(self, params={}, callback=None):
        self._request(
            'GET',
            'https://slack.com/api/conversations.history',
            {'token': self._token, **params},
            callback
        )

    def emoji_list(self, params={}, callback=None):
        self._request(
            'GET',
            'https://slack.com/api/emoji.list',
            {'token': self._token, **params},
            callback
        )

    def groups_info(self, params={}, callback=None):
        self._request(
            'GET',
            'https://slack.com/api/groups.info',
            {'token': self._token, **params},
            callback
        )

    def groups_leave(self, params={}, callback=None):
        self._request(
            'POST',
            'https://slack.com/api/groups.leave',
            {'token': self._token, **params},
            callback
        )

    def groups_mark(self, params={}, callback=None):
        self._request(
            'POST',
            'https://slack.com/api/groups.mark',
            {'token': self._token, **params},
            callback
        )

    def im_close(self, params={}, callback=None):
        self._request(
            'POST',
            'https://slack.com/api/im.close',
            {'token': self._token, **params},
            callback
        )

    def im_mark(self, params={}, callback=None):
        self._request(
            'POST',
            'https://slack.com/api/im.mark',
            {'token': self._token, **params},
            callback
        )

    def im_open(self, params={}, callback=None):
        self._request(
            'POST',
            'https://slack.com/api/im.open',
            {'token': self._token, **params},
            callback
        )

    def mpim_close(self, params={}, callback=None):
        self._request(
            'POST',
            'https://slack.com/api/mpim.close',
            {'token': self._token, **params},
            callback
        )

    def mpim_mark(self, params={}, callback=None):
        self._request(
            'POST',
            'https://slack.com/api/mpim.mark',
            {'token': self._token, **params},
            callback
        )

    def mpim_open(self, params={}, callback=None):
        self._request(
            'POST',
            'https://slack.com/api/mpim.open',
            {'token': self._token, **params},
            callback
        )

    def rtm_start(self, params={}, callback=None):
        self._request(
            'GET',
            'https://slack.com/api/rtm.start',
            {'token': self._token, **params},
            callback
        )

    def _request(self, method, url, params={}, callback=None):
        request = Soup.form_request_new_from_hash(method, url, params)

        def finish(session, message):
            if callback:
                return callback(json.loads(message.response_body.data))
        self._soup.queue_message(request, finish)


class SlackRtmClient:
    def __init__(self):
        self._soup = Soup.Session()
        self._web = SlackWebClient()

    def presence_sub(self, ids):
        self._connection.send_text(json.dumps({
            'type': 'presence_sub',
            'ids': ids
        }))

    def run(self, on_start, on_message):
        self._on_start = on_start
        self._on_message = on_message
        self._web.rtm_start({'mpim_aware': 'true'}, self._on_rtm_start)

    def _on_rtm_start(self, start_response):
        self._start_response = start_response
        message = Soup.Message.new('GET', start_response['url'])
        self._soup.websocket_connect_async(
            message,
            'https://slack.com',
            None,
            None,
            self._on_websocket_connect
        )

    def _on_websocket_connect(self, session, result):
        self._connection = session.websocket_connect_finish(result)
        self._connection.connect('message', self._on_websocket_message)

    def _on_websocket_message(self, _connection, _type, message):
        data = json.loads(message.get_data())
        if data['type'] == 'hello':
            self._on_start(self._start_response)
        else:
            self._on_message(data)
