from gi.repository import Gtk

from glack.widgets.channel_sidebar_row import ChannelSidebarRow


@Gtk.Template(resource_path='/com/gitlab/lnovsak/Glack/ui/channel_sidebar.ui')
class ChannelSidebar(Gtk.Box):
    __gtype_name__ = 'ChannelSidebar'

    header = Gtk.Template.Child()
    users = Gtk.Template.Child()

    def __init__(self, ws, model):
        super().__init__()

        self._ws = ws
        self._model = model

        self._set_header()

        self._model.members.connect('items-changed', self._on_members_changed)

        self.users.bind_model(self._model.members, self._on_member_added)

    def _on_member_added(self, user):
        return ChannelSidebarRow(self._ws, user)

    def _on_members_changed(self, *_):
        self._set_header()
        self.header.show()

    def _set_header(self):
        self.header.set_text('Members ({})'.format(len(self._model.members)))
