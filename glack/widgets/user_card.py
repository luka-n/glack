from gi.repository import GdkPixbuf, GLib, Gtk

from glack.avatar_cache import AvatarCache


@Gtk.Template(resource_path='/com/gitlab/lnovsak/Glack/ui/user_card.ui')
class UserCard(Gtk.Box):
    __gtype_name__ = 'UserCard'

    avatar = Gtk.Template.Child()
    header_icon = Gtk.Template.Child()
    header_label = Gtk.Template.Child()
    message_button = Gtk.Template.Child()
    title = Gtk.Template.Child()

    def __init__(self, ws, model):
        super().__init__()

        self._ws = ws
        self._model = model

        self._set_avatar()
        self._set_header_icon()
        self._set_header_label()
        self._set_title()

        self._model.connect('notify', self._on_model_changed)

        self.message_button.connect('clicked', self._on_message_button_clicked)

    def _on_avatar_get(self, path):
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(path) \
            .scale_simple(250, 250, GdkPixbuf.InterpType.BILINEAR)
        self.avatar.set_from_pixbuf(pixbuf)
        self.avatar.show()

    def _on_message_button_clicked(self, _):
        action = self.get_action_group('win').lookup_action('open-dm')
        action.activate(GLib.Variant.new_string(self._model.id))

    def _on_model_changed(self, _, param):
        if param.name == 'avatar':
            self._set_avatar()
        elif param.name == 'presence':
            self._set_header_icon()
            self.header_icon.show()
        elif param.name == 'name':
            self._set_header_label()
            self.header_label.show()
        elif param.name == 'title':
            self._set_title()
            self.title.show()

    def _set_avatar(self):
        AvatarCache().get(
            self._model.avatar.avatar_hash,
            self._model.avatar.avatar_url,
            self._on_avatar_get
        )

    def _set_header_icon(self):
        icon_name = {
            'active': 'user-available-symbolic',
            'away': 'user-offline-symbolic'
        }[self._model.presence]
        self.header_icon.set_from_icon_name(icon_name, 16)

    def _set_header_label(self):
        self.header_label.set_text(self._model.name)

    def _set_title(self):
        if self._model.title:
            self.title.set_text(self._model.title)
        else:
            self.title.hide()
