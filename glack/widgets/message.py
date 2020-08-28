import math

from datetime import datetime, timezone
from gi.repository import Gdk, GdkPixbuf, Gtk, Pango

from glack.avatar_cache import AvatarCache
from glack.mrkdwn import Mrkdwn
from glack.url_preview import ImageUrlPreview, UrlPreview

from glack.widgets.user_card import UserCard


def leaves_with_modifiers(root):
    nodes = []
    for child in root['children']:
        if 'children' in child:
            for leaf in leaves_with_modifiers(child):
                nodes.append((leaf[0], [root['type'], *leaf[1]]))
        else:
            nodes.append((child, [root['type']]))
    return nodes


def modifiers_to_tag_names(modifiers):
    mapping = {
        'BOLD': 'bold',
        'ITALIC': 'italic',
        'QUOTE': 'quote',
        'STRIKE': 'strike'
    }
    return [mapping[m] for m in modifiers if not m == 'ROOT']


def parse_ts(ts):
    return datetime \
        .utcfromtimestamp(float(ts)) \
        .replace(tzinfo=timezone.utc) \
        .astimezone(tz=None)


@Gtk.Template(resource_path='/com/gitlab/lnovsak/Glack/ui/message.ui')
class Message(Gtk.ListBoxRow):
    __gtype_name__ = 'Message'

    avatar = Gtk.Template.Child()
    avatar_event_box = Gtk.Template.Child()
    message = Gtk.Template.Child()
    time = Gtk.Template.Child()
    url_previews = Gtk.Template.Child()
    user = Gtk.Template.Child()
    user_card = None
    user_event_box = Gtk.Template.Child()
    user_popover = Gtk.Template.Child()

    def __init__(self, ws, model):
        super().__init__()

        self._ws = ws
        self._model = model

        self.user_card = UserCard(self._ws, self._model.user)
        self.user_popover.add(self.user_card)

        self._create_tags()

        self._set_avatar()
        self._set_message()
        self._set_time()
        self._set_user()

        self._set_unread_class()

        self._model.connect('notify', self._on_model_changed)
        self._model.channel.connect('notify', self._on_channel_changed)
        self._model.user.connect('notify', self._on_user_changed)

        self.avatar_event_box.connect(
            'button-press-event', self._on_avatar_button_press
        )

        self.user_event_box.connect(
            'button-press-event', self._on_user_button_press
        )

    def set_text(self, text):
        mrkdwn = Mrkdwn(text)
        root = mrkdwn.parse()

        self._clear_text()

        for node, modifiers in leaves_with_modifiers(root):
            tag_names = modifiers_to_tag_names(modifiers)

            if node['type'] == 'CHANNEL_LINK':
                self._insert_channel_link(node['value'], tag_names)
            elif node['type'] == 'CODE':
                self._insert_code(node['value'], tag_names)
            elif node['type'] == 'EMOJI':
                self._insert_emoji(node['value'], tag_names)
            elif node['type'] == 'PRE':
                self._insert_pre(node['value'], tag_names)
            elif node['type'] == 'TEXT':
                self._insert_text(node['value'], tag_names)
            elif node['type'] == 'URL':
                self._insert_url(node['value'], node['label'], tag_names)
            elif node['type'] == 'USER_LINK':
                self._insert_user_link(node['value'], tag_names)

    def _add_url_preview(self, url):
        def handle_preview(preview):
            if isinstance(preview, ImageUrlPreview):
                image = Gtk.Image.new_from_pixbuf(preview.pixbuf)
                self.url_previews.add(image)
                self.url_previews.show_all()

        UrlPreview.new_from_url(url, handle_preview)

    def _clear_text(self):
        buf = self.message.get_buffer()
        buf.set_text('', -1)

    def _create_tags(self):
        link_color = self._get_link_color()
        buf = self.message.get_buffer()
        self._bold_tag = buf.create_tag('bold', weight=Pango.Weight.BOLD)
        self._code_tag = buf.create_tag('code', font='monospace')
        self._italic_tag = buf.create_tag('italic', style=Pango.Style.ITALIC)
        self._link_tag = buf.create_tag('link', foreground_rgba=link_color)
        self._pre_tag = buf.create_tag('pre', font='monospace')
        self._quote_tag = buf.create_tag('quote')
        self._strike_tag = buf.create_tag('strike', strikethrough=True)

    def _get_link_color(self):
        context = self.get_style_context()
        context.save()
        context.set_state(Gtk.StateFlags.LINK)
        color = context.get_color(context.get_state())
        context.restore()
        return color

    def _insert_channel_link(self, channel_id, tag_names=[]):
        if self._ws.has_channel(channel_id):
            channel = self._ws.get_channel(channel_id)
            self._insert_text('#{}'.format(channel.name), ['link', *tag_names])
        else:
            self._insert_text('<#{}>'.format(channel_id), tag_names)

    def _insert_code(self, text, tag_names):
        self._insert_text(text, ['code', *tag_names])

    def _insert_emoji(self, name, tag_names=[]):
        pixbuf = self._ws.emoji_loader.get_pixbuf(name, 22)
        buf = self.message.get_buffer()
        if pixbuf:
            buf.insert_pixbuf(buf.get_end_iter(), pixbuf)
        else:
            self._insert_text(':{}:'.format(name), tag_names)

    def _insert_pre(self, text, tag_names=[]):
        self._insert_text(text, ['pre', *tag_names])

    def _insert_text(self, text, tag_names=[]):
        buf = self.message.get_buffer()
        buf.insert_with_tags_by_name(buf.get_end_iter(), text, *tag_names)

    def _insert_url(self, url, label=None, tag_names=[]):
        self._insert_text(url, ['link', *tag_names])
        self._add_url_preview(url)

    def _insert_user_link(self, user_id, tag_names=[]):
        if self._ws.has_user(user_id):
            user = self._ws.get_user(user_id)
            self._insert_text('@{}'.format(user.name), ['link', *tag_names])
        else:
            self._insert_text('<@{}>'.format(user_id), tag_names)

    def _on_avatar_button_press(self, _, event):
        if event.button == 1:
            self.user_popover.set_relative_to(self.avatar_event_box)
            self.user_popover.popup()

    def _on_avatar_get(self, path):
        def draw(_, context):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(path) \
                .scale_simple(36, 36, GdkPixbuf.InterpType.BILINEAR)
            surface = Gdk.cairo_surface_create_from_pixbuf(pixbuf, 1)
            context.set_source_surface(surface)
            context.arc(18.0, 18.0, 18.0, 0.0, 2 * math.pi)
            context.clip()
            context.paint()
        self.avatar.connect('draw', draw)

    def _on_channel_changed(self, _, prop):
        if prop.name == 'last_read':
            self._set_unread_class()

    def _on_model_changed(self, _, prop):
        if prop.name == 'text':
            self._set_message()
            self.message.show()

    def _on_user_button_press(self, _, event):
        if event.button == 1:
            self.user_popover.set_relative_to(self.user_event_box)
            self.user_popover.popup()

    def _on_user_changed(self, _, prop):
        if prop.name == 'name':
            self._set_user()
            self.user.show()

    def _set_avatar(self):
        AvatarCache().get(
            self._model.user.avatar.avatar_hash,
            self._model.user.avatar.avatar_url,
            self._on_avatar_get
        )

    def _set_message(self):
        self.set_text(self._model.text)

    def _set_time(self):
        time = parse_ts(self._model.ts)
        self.time.set_text(time.strftime('%H:%M'))

    def _set_unread_class(self):
        if self._model.ts > self._model.channel.last_read:
            self.get_style_context().add_class('message--unread')
        else:
            self.get_style_context().remove_class('message--unread')

    def _set_user(self):
        self.user.set_text(self._model.user.name)
