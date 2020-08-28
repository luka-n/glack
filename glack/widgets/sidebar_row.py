from gi.repository import Gdk, Gio, Gtk

from glack.models.channel import (
    ImChannel, MpimChannel, PublicChannel, PrivateChannel
)


@Gtk.Template(resource_path='/com/gitlab/lnovsak/Glack/ui/sidebar_row.ui')
class SidebarRow(Gtk.ListBoxRow):
    __gtype_name__ = 'SidebarRow'

    event_box = Gtk.Template.Child()
    icon = Gtk.Template.Child()
    label = Gtk.Template.Child()
    popover = Gtk.Template.Child()

    def __init__(self, ws, model):
        super().__init__()

        self._ws = ws
        self._model = model

        self._set_icon()
        self._set_label()
        self._set_unread_class()

        self.popover.bind_model(self._build_menu())

        self._model.connect('notify', self._on_model_changed)

        if isinstance(self._model, ImChannel):
            self._model.user.connect('notify', self._on_user_model_changed)

        self.event_box.connect('button-press-event', self._on_button_press)

        self._model.load_latest()

    def _build_menu(self):
        menu = Gio.Menu()
        if isinstance(self._model, (PrivateChannel, PublicChannel)):
            menu.append(
                'Leave', 'win.leave-channel("{}")'.format(self._model.id)
            )
        else:
            menu.append(
                'Close', 'win.close-channel("{}")'.format(self._model.id)
            )
        return menu

    def _on_button_press(self, _, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            self.popover.popup()

    def _on_model_changed(self, _, param):
        if param.name == 'name':
            self._set_label()
            self.label.show()
        elif param.name == 'latest' or param.name == 'last_read':
            self._set_unread_class()

    def _on_user_model_changed(self, _, param):
        if param.name == 'presence':
            self._set_icon()
            self.icon.show()

    def _set_icon(self):
        if isinstance(self._model, ImChannel):
            icon_name = {
                'active': 'user-available-symbolic',
                'away': 'user-offline-symbolic'
            }[self._model.user.presence]
        else:
            icon_name = {
                MpimChannel: 'system-users-symbolic',
                PrivateChannel: 'system-lock-screen-symbolic',
                PublicChannel: 'network-workgroup-symbolic'
            }[type(self._model)]
        self.icon.set_from_icon_name(icon_name, 16)

    def _set_label(self):
        self.label.set_text(self._model.name)

    def _set_unread_class(self):
        if self._model.latest and self._model.latest > self._model.last_read:
            self.get_style_context().add_class('sidebar_row--unread')
        else:
            self.get_style_context().remove_class('sidebar_row--unread')
