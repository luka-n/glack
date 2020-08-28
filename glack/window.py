from gi.repository import GLib, Gio, Gtk

from glack.workspace import Workspace

from glack.widgets.channel import Channel
from glack.widgets.composer import Composer
from glack.widgets.join_channel_dialog import JoinChannelDialog
from glack.widgets.open_dm_dialog import OpenDmDialog
from glack.widgets.sidebar import Sidebar


@Gtk.Template(resource_path='/com/gitlab/lnovsak/Glack/ui/window.ui')
class Window(Gtk.ApplicationWindow):
    __gtype_name__ = 'Window'

    channel_header_bar = Gtk.Template.Child()
    channel_menu_button = Gtk.Template.Child()
    channel_sidebar_button = Gtk.Template.Child()
    channels_stack = Gtk.Template.Child()
    main = Gtk.Template.Child()
    paned = Gtk.Template.Child()
    paned_header = Gtk.Template.Child()
    sidebar_header_bar = Gtk.Template.Child()
    sidebar_menu_button = Gtk.Template.Child()
    sidebar_viewport = Gtk.Template.Child()
    sidebar_window = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.sidebar_viewport.set_focus_hadjustment(
            self.sidebar_window.get_hadjustment()
        )
        self.sidebar_viewport.set_focus_vadjustment(
            self.sidebar_window.get_vadjustment()
        )

        self._stack_channels = {}
        self._ws = Workspace()

        self.composer = Composer(self._ws)
        self.main.add(self.composer)

        self.composer.connect('activate', self._on_composer_activate)

        self._sidebar = Sidebar(self._ws)
        self.sidebar_viewport.add(self._sidebar)

        self._sidebar.connect('row-activated', self._on_channel_activated)

        self.channel_sidebar_button.connect(
            'clicked', self._on_channel_sidebar_button_clicked
        )

        self.paned.connect('notify::position', self._on_paned_position_change)
        self.paned_header.connect(
            'notify::position', self._on_paned_header_position_change
        )

        self._ws.connect('started', self._on_ws_started)

        self._ws.start()

        self.channel_menu_button.set_menu_model(self._build_channel_menu())
        self.sidebar_menu_button.set_menu_model(self._build_sidebar_menu())
        self._add_actions()

    def open_channel(self, channel_id):
        if channel_id in self._stack_channels:
            channel = self._stack_channels[channel_id]
        else:
            channel = Channel(self._ws, self._ws.get_channel(channel_id))
            self.channels_stack.add(channel)
            self._stack_channels[channel_id] = channel

        self.channels_stack.set_visible_child(channel)
        self.channels_stack.show_all()

        self.channel_header_bar.set_title(channel._model.name)
        self.channel_header_bar.set_subtitle(channel._model.topic)

    def _add_actions(self):
        actions = [
            {
                'name': 'close-channel',
                'activate': self._on_close_channel,
                'arg_type': GLib.VariantType.new('s')
            },
            {
                'name': 'join-channel',
                'activate': self._on_join_channel
            },
            {
                'name': 'leave-channel',
                'activate': self._on_leave_channel,
                'arg_type': GLib.VariantType.new('s')
            },
            {
                'name': 'mark-read',
                'activate': self._on_mark_read
            },
            {
                'name': 'open-dm',
                'activate': self._on_open_dm,
                'arg_type': GLib.VariantType.new('s')
            },
            {
                'name': 'open-dm-dialog',
                'activate': self._on_open_dm_dialog
            }
        ]
        for action in actions:
            if 'arg_type' in action:
                arg_type = action['arg_type']
            else:
                arg_type = None
            gio_action = Gio.SimpleAction.new(action['name'], arg_type)
            gio_action.connect('activate', action['activate'])
            self.add_action(gio_action)

    def _build_channel_menu(self):
        menu = Gio.Menu()
        menu.append('Mark read', 'win.mark-read')
        return menu

    def _build_sidebar_menu(self):
        menu = Gio.Menu()
        menu.append('Join channel', 'win.join-channel')
        menu.append('Open direct message', 'win.open-dm-dialog')
        return menu

    def _on_channel_activated(self, _, row):
        self.open_channel(row._model.id)

    def _on_channel_sidebar_button_clicked(self, _):
        channel = self.channels_stack.get_visible_child()
        channel.toggle_sidebar()

    def _on_close_channel(self, _, arg):
        channel_id = arg.get_string()
        self._ws.get_channel(channel_id).close()

    def _on_composer_activate(self, _):
        channel = self.channels_stack.get_visible_child()
        text = self.composer.get_text()
        channel._model.post_message(text)
        self.composer.clear()

    def _on_join_channel(self, *a):
        dialog = JoinChannelDialog(self, self._ws)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            channel = dialog.get_selected_channel()
            self._ws.web.channels_join({'name': '#{}'.format(channel.name)})
        dialog.destroy()

    def _on_leave_channel(self, _, arg):
        channel_id = arg.get_string()
        self._ws.get_channel(channel_id).leave()

    def _on_mark_read(self, *_):
        channel = self.channels_stack.get_visible_child()._model
        channel.mark_read()

    def _on_open_dm(self, _, arg):
        user_id = arg.get_string()
        self._ws.web.im_open({'user': user_id})

    def _on_open_dm_dialog(self, *_):
        dialog = OpenDmDialog(self, self._ws)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            users = dialog.get_selected_users()
            if len(users) > 1:
                self._ws.web.mpim_open({
                    'users': ','.join([u.id for u in users])
                })
            else:
                self._ws.web.im_open({'user': users[0].id})
        dialog.destroy()

    def _on_paned_position_change(self, *_):
        self.paned_header.set_position(self.paned.get_position())

    def _on_paned_header_position_change(self, *_):
        self.paned.set_position(self.paned_header.get_position())

    def _on_ws_started(self, _):
        self.sidebar_header_bar.set_title(self._ws.current_team['name'])
        general = next(
            channel
            for channel in self._ws.channels
            if channel.name == 'general'
        )
        self.open_channel(general.id)
        self.composer.grab_focus()
