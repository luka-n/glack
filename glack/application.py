import gi

gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Gtk', '3.0')
gi.require_version('Soup', '2.4')

from gi.repository import Gdk, Gtk, Gio  # noqa: E420

from glack.window import Window  # noqa: E402


class Application(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id='com.gitlab.lnovsak.Glack',
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )

        self._add_css_provider()

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = Window(application=self)
        win.present()

    def _add_css_provider(self):
        provider = Gtk.CssProvider()
        uri = 'resource:///com/gitlab/lnovsak/Glack/css/application.css'

        provider.load_from_file(Gio.File.new_for_uri(uri))

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
