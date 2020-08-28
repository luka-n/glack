from gi.repository import Gtk


@Gtk.Template(resource_path='/com/gitlab/lnovsak/Glack/ui/open_dm_dialog.ui')
class OpenDmDialog(Gtk.Dialog):
    __gtype_name__ = 'OpenDmDialog'

    search = Gtk.Template.Child()
    users = Gtk.Template.Child()

    def __init__(self, parent, ws):
        super().__init__(
            'Open direct message',
            parent,
            0,
            (
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK,     Gtk.ResponseType.OK
            ),
            use_header_bar=1
        )

        self._ws = ws

        self.users.set_filter_func(self._filter_func)
        self.users.set_sort_func(self._sort_func)

        self.search.connect('search-changed', self._on_search_changed)
        self.users.connect('row-activated', self._on_row_activated)

        for user in ws.users:
            row = Gtk.ListBoxRow()
            row._model = user
            box = Gtk.Box()
            check = Gtk.CheckButton()
            label = Gtk.Label(user.name, xalign=0.0)
            box.add(check)
            box.add(label)
            row.add(box)
            self.users.add(row)

        self.show_all()

    def get_selected_users(self):
        return [
            row._model
            for row in self.users.get_children()
            if row.get_child().get_children()[0].get_active()
        ]

    def _filter_func(self, row):
        search = self.search.get_text()
        if not search:
            return True
        return search.lower() in row._model.name.lower()

    def _on_row_activated(self, _, row):
        check = row.get_child().get_children()[0]
        check.set_active(not check.get_active())

    def _on_search_changed(self, _):
        self.users.invalidate_filter()

    def _sort_func(self, a, b):
        aname = a._model.name.lower()
        bname = b._model.name.lower()
        if aname == bname:
            return 0
        else:
            return 1 if aname > bname else -1
