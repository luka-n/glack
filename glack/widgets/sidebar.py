from gi.repository import Gtk, Pango

from glack.models.channel import PrivateChannel, PublicChannel

from glack.widgets.sidebar_row import SidebarRow


@Gtk.Template(resource_path='/com/gitlab/lnovsak/Glack/ui/sidebar.ui')
class Sidebar(Gtk.ListBox):
    __gtype_name__ = 'Sidebar'

    def __init__(self, ws):
        super().__init__()

        self._ws = ws

        self.set_filter_func(self._filter_func)
        self.set_header_func(self._header_func)
        self.set_sort_func(self._sort_func)

        self._ws.connect('channel-added', self._on_channel_added)

    def _filter_func(self, row):
        return row._model.is_open

    def _header_func(self, row, before):
        if isinstance(row._model, (PublicChannel, PrivateChannel)):
            heading = 'Channels'
        else:
            heading = 'Direct Messages'
        if before:
            if isinstance(before._model, (PublicChannel, PrivateChannel)):
                before_heading = 'Channels'
            else:
                before_heading = 'Direct Messages'
            if heading == before_heading:
                if row.get_header():
                    row.get_header().destroy()
                return
        label = Gtk.Label(
            heading, ellipsize=Pango.EllipsizeMode.END, xalign=0.0
        )
        label.get_style_context().add_class('sidebar__header')
        row.set_header(label)

    def _on_channel_added(self, _, channel):
        row = SidebarRow(self._ws, channel)

        self.add(row)

        channel.connect('notify::is-open', self._on_channel_is_open_changed)

        self.show_all()

    def _on_channel_is_open_changed(self, _, channel):
        self.invalidate_filter()

    def _sort_func(self, a, b):
        if isinstance(a._model, (PublicChannel, PrivateChannel)):
            akind = 'Channels'
        else:
            akind = 'Direct Messages'
        if isinstance(b._model, (PublicChannel, PrivateChannel)):
            bkind = 'Channels'
        else:
            bkind = 'Direct Messages'
        if akind != bkind:
            return 1 if akind > bkind else -1

        aname = a._model.name.lower()
        bname = b._model.name.lower()
        if aname == bname:
            return 0
        else:
            return 1 if aname > bname else -1
