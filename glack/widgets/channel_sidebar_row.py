from gi.repository import Gio, Gtk

from glack.widgets.user_card import UserCard


@Gtk.Template(resource_path='/com/gitlab/lnovsak/Glack/ui/channel_sidebar_row.ui')  # noqa: E501
class ChannelSidebarRow(Gtk.ListBoxRow):
    __gtype_name__ = 'ChannelSidebarRow'

    card_popover = Gtk.Template.Child()
    event_box = Gtk.Template.Child()
    icon = Gtk.Template.Child()
    label = Gtk.Template.Child()
    menu_popover = Gtk.Template.Child()
    user_card = None

    def __init__(self, ws, model):
        super().__init__()

        self._ws = ws
        self._model = model

        self.user_card = UserCard(self._ws, self._model)
        self.card_popover.add(self.user_card)

        self._set_icon()
        self._set_label()

        self._model.connect('notify', self._on_model_changed)

        self.event_box.connect('button-press-event', self._on_button_press)

        self.menu_popover.bind_model(self._build_menu())

    def _build_menu(self):
        menu = Gio.Menu()
        menu.append('Message', 'win.open-dm("{}")'.format(self._model.id))
        return menu

    def _on_button_press(self, _, event):
        if event.button == 1:
            self.card_popover.popup()
        elif event.button == 3:
            self.menu_popover.popup()

    def _on_model_changed(self, _, param):
        if param.name == 'name':
            self._set_label()
            self.label.show()
        elif param.name == 'presence':
            self._set_icon()
            self.icon.show()

    def _set_icon(self):
        icon_name = {
            'active': 'user-available-symbolic',
            'away': 'user-offline-symbolic'
        }[self._model.presence]
        self.icon.set_from_icon_name(icon_name, 16)

    def _set_label(self):
        self.label.set_text(self._model.name)
