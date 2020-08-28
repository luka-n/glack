from gi.repository import Gtk
from glack.models.channel import PublicChannel


@Gtk.Template(resource_path='/com/gitlab/lnovsak/Glack/ui/join_channel_dialog.ui')  # noqa: E501
class JoinChannelDialog(Gtk.Dialog):
    __gtype_name__ = 'JoinChannelDialog'

    channels = Gtk.Template.Child()
    search = Gtk.Template.Child()

    def __init__(self, parent, ws):
        super().__init__(
            'Join channel',
            parent,
            0,
            (
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK,     Gtk.ResponseType.OK
            ),
            use_header_bar=1
        )

        self._ws = ws

        self.channels.set_filter_func(self._filter_func)
        self.channels.set_sort_func(self._sort_func)

        self.search.connect('search-changed', self._on_search_changed)

        for channel in ws.channels:
            if isinstance(channel, PublicChannel) and not channel.is_open:
                row = Gtk.ListBoxRow()
                row._model = channel
                label = Gtk.Label(channel.name, xalign=0.0)
                row.add(label)
                self.channels.add(row)

        self.show_all()

    def get_selected_channel(self):
        return self.channels.get_selected_row()._model

    def _filter_func(self, row):
        search = self.search.get_text()
        if not search:
            return True
        return True if search.lower() in row._model.name.lower() else False

    def _on_search_changed(self, _):
        self.channels.invalidate_filter()

    def _sort_func(self, a, b):
        aname = a._model.name.lower()
        bname = b._model.name.lower()
        if aname == bname:
            return 0
        else:
            return 1 if aname > bname else -1
