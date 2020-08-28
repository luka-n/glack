from gi.repository import Gtk

from glack.widgets.channel_sidebar import ChannelSidebar
from glack.widgets.message import Message


@Gtk.Template(resource_path='/com/gitlab/lnovsak/Glack/ui/channel.ui')
class Channel(Gtk.Paned):
    __gtype_name__ = 'Channel'

    messages = Gtk.Template.Child()
    messages_viewport = Gtk.Template.Child()
    messages_window = Gtk.Template.Child()
    sidebar = None
    sidebar_viewport = Gtk.Template.Child()
    sidebar_window = Gtk.Template.Child()

    def __init__(self, ws, model):
        super().__init__()

        self._fix_adjustments()

        self._ws = ws
        self._model = model

        self.sidebar = ChannelSidebar(self._ws, self._model)
        self.sidebar_viewport.add(self.sidebar)

        self.messages.bind_model(self._model.messages, self._on_message_added)

        self.messages_window.get_vadjustment().connect(
            'changed', self._on_messages_window_vadjustment_changed
        )

        self._model.load_history()

    def toggle_sidebar(self):
        if self.sidebar_window.is_visible():
            self.sidebar_window.hide()
        else:
            self.sidebar_window.show()

    def _fix_adjustments(self):
        self.messages_viewport.set_focus_hadjustment(
            self.messages_window.get_hadjustment())
        self.messages_viewport.set_focus_vadjustment(
            self.messages_window.get_vadjustment())
        self.sidebar_viewport.set_focus_hadjustment(
            self.sidebar_window.get_hadjustment())
        self.sidebar_viewport.set_focus_vadjustment(
            self.sidebar_window.get_vadjustment())

    def _on_message_added(self, message):
        return Message(self._ws, message)

    def _on_messages_window_vadjustment_changed(self, _):
        self.messages_window.get_vadjustment().set_value(
            self.messages_window.get_vadjustment().get_upper()
        )
