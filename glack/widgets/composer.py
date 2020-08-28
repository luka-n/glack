from gi.repository import Gdk, GObject, Gtk

from glack.models.channel import PublicChannel


@Gtk.Template(resource_path='/com/gitlab/lnovsak/Glack/ui/composer.ui')
class Composer(Gtk.Box):
    __gtype_name__ = 'Composer'

    __gsignals__ = {
        'activate': (GObject.SignalFlags.RUN_FIRST, None, ())
    }

    completions = Gtk.Template.Child()
    completions_popover = Gtk.Template.Child()
    completions_title = Gtk.Template.Child()
    completions_viewport = Gtk.Template.Child()
    completions_window = Gtk.Template.Child()
    emoji_button = Gtk.Template.Child()
    entry = Gtk.Template.Child()

    def __init__(self, ws):
        super().__init__()

        self._fix_adjustments()

        self._ws = ws

        self._buffer = self.entry.get_buffer()

        self.completions.set_filter_func(self._completions_filter_func)
        self.completions.set_sort_func(self._completions_sort_func)

        self._completion_candidate = None
        self._completions = []

        self._set_completions()

        self._ws.connect('channel-added', self._on_channel_added)
        self._ws.connect('emoji-added', self._on_emoji_added)
        self._ws.connect('user-added', self._on_user_added)

        self.connect('size-allocate', self._on_size_allocate)

        self._buffer.connect('changed', self._on_buffer_changed)

        self.completions.connect('row-activated', self._on_completion_activated)

        self.emoji_button.connect('clicked', self._on_emoji_button_clicked)

        self.entry.connect('focus-in-event', self._on_entry_focus_in)
        self.entry.connect('focus-out-event', self._on_entry_focus_out)

        self.entry.connect('key-press-event', self._on_entry_key_press)

    def clear(self):
        self._buffer.set_text('', -1)

    def get_text(self):
        data = self._buffer.get_slice(
            self._buffer.get_start_iter(),
            self._buffer.get_end_iter(),
            True
        )
        text = ''
        for index, char in enumerate(data):
            if ord(char) == 0xfffc:
                pixbuf = self._buffer.get_iter_at_offset(index).get_pixbuf()
                if pixbuf:
                    text += ':{}:'.format(pixbuf._name)
                else:
                    text += char
            else:
                text += char
        return text

    def grab_focus(self):
        self.entry.grab_focus()

    def _build_completion_row(self, completion):
        row = Gtk.ListBoxRow()
        row._completion = completion

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        if completion.startswith(':'):
            pixbuf = self._ws.emoji_loader.get_pixbuf(completion[1:-1], 16)
            image = Gtk.Image.new_from_pixbuf(pixbuf)
            box.add(image)

        label = Gtk.Label(completion, xalign=0.0)

        box.add(label)

        row.add(box)

        return row

    def _completions_activate(self):
        self.completions.emit('activate-cursor-row')
        self.grab_focus()

    def _completions_filter_func(self, row):
        if not self._completion_candidate:
            return False
        c = row._completion.lower()
        cc = self._completion_candidate.lower()
        return c.startswith(cc)

    def _completions_first(self):
        self.completions.emit('move-cursor', Gtk.MovementStep.BUFFER_ENDS, -1)
        self.grab_focus()

    def _completions_last(self):
        self.completions.emit('move-cursor', Gtk.MovementStep.BUFFER_ENDS, 0)
        self.grab_focus()

    def _completions_next(self):
        self.completions.emit('move-cursor', Gtk.MovementStep.DISPLAY_LINES, 1)
        self.grab_focus()

    def _completions_page_down(self):
        self.completions.emit('move-cursor', Gtk.MovementStep.PAGES, -1)
        self.grab_focus()

    def _completions_page_up(self):
        self.completions.emit('move-cursor', Gtk.MovementStep.PAGES, 1)
        self.grab_focus()

    def _completions_prev(self):
        self.completions.emit('move-cursor', Gtk.MovementStep.DISPLAY_LINES, -1)
        self.grab_focus()

    def _completions_sort_func(self, a, b):
        aname = a._completion.lower()
        bname = b._completion.lower()
        if aname == bname:
            return 0
        else:
            return 1 if aname > bname else -1

    def _find_completion_candidate(self):
        end_idx = self._buffer.props.cursor_position
        point_iter = self._buffer.get_iter_at_offset(end_idx)
        text = self._buffer.get_text(
            self._buffer.get_start_iter(), point_iter, False
        )
        start_idx = next(
            (
                idx
                for idx, char in reversed(list(enumerate(text)))
                if char in '#:@'
            ),
            None
        )
        if start_idx is not None:
            return text[start_idx:end_idx]

    def _fix_adjustments(self):
        self.completions_viewport.set_focus_hadjustment(
            self.completions_window.get_hadjustment()
        )
        self.completions_viewport.set_focus_vadjustment(
            self.completions_window.get_vadjustment()
        )

    def _has_completions(self):
        if not self._completion_candidate:
            return False

        for completion in self._completions:
            c = completion.lower()
            cc = self._completion_candidate.lower()
            if c.startswith(cc) and len(c) > len(cc):
                return True

        return False

    def _hide_completions(self):
        self.completions_popover.popdown()
        self.completions.select_row(None)

    def _insert_completion(self, completion):
        start_iter = self._buffer.get_iter_at_offset(
            self._buffer.props.cursor_position - len(self._completion_candidate)
        )
        point_iter = self._buffer.get_iter_at_offset(
            self._buffer.props.cursor_position
        )

        self._buffer.delete(start_iter, point_iter)

        if completion.startswith(':'):
            self._insert_emoji(completion[1:-1])
        else:
            self._buffer.insert(point_iter, completion, -1)

    def _insert_emoji(self, name):
        pixbuf = self._ws.emoji_loader.get_pixbuf(name, 22)
        point_iter = self._buffer.get_iter_at_offset(
            self._buffer.props.cursor_position
        )
        self._buffer.insert_pixbuf(point_iter, pixbuf)

    def _on_buffer_changed(self, *_):
        self._completion_candidate = self._find_completion_candidate()

        if self._has_completions():
            self.completions_title.set_text(
                'Completions for "{}"'.format(self._completion_candidate)
            )
            self.completions_title.show()

            self.completions.invalidate_filter()

            self._show_completions()
        else:
            self._hide_completions()

    def _on_channel_added(self, _, channel):
        if isinstance(channel, PublicChannel) and channel.is_open:
            completion = '#{}'.format(channel.name)
            self._completions.append(completion)
            row = self._build_completion_row(completion)
            self.completions.add(row)
            self.completions.show_all()

    def _on_completion_activated(self, _, row):
        self.grab_focus()
        self._insert_completion(row._completion)

    def _on_emoji_added(self, _, emoji):
        completion = ':{}:'.format(emoji.name)
        self._completions.append(completion)
        row = self._build_completion_row(completion)
        self.completions.add(row)
        self.completions.show_all()

    def _on_emoji_button_clicked(self, _):
        self._buffer.insert_at_cursor(':', -1)

    def _on_entry_focus_in(self, *_):
        self.get_style_context().add_class('composer--focused')

    def _on_entry_focus_out(self, *_):
        self.get_style_context().remove_class('composer--focused')

    def _on_entry_key_press(self, _, event):
        is_shift = event.state & Gdk.ModifierType.SHIFT_MASK
        keyval = event.keyval

        completions_handlers = {
            Gdk.KEY_Down:      self._completions_next,
            Gdk.KEY_End:       self._completions_last,
            Gdk.KEY_Escape:    self._hide_completions,
            Gdk.KEY_Home:      self._completions_first,
            Gdk.KEY_Page_Down: self._completions_page_up,
            Gdk.KEY_Page_Up:   self._completions_page_down,
            Gdk.KEY_Tab:       self._completions_next,
            Gdk.KEY_Up:        self._completions_prev
        }

        if self.completions_popover.is_visible():
            if keyval in completions_handlers:
                completions_handlers[keyval]()
                return Gdk.EVENT_STOP

            if keyval == Gdk.KEY_Return and not is_shift:
                self._completions_activate()
                return Gdk.EVENT_STOP

        if keyval == Gdk.KEY_Return and not is_shift:
            self.emit('activate')
            return Gdk.EVENT_STOP

        return Gdk.EVENT_PROPAGATE

    def _on_size_allocate(self, _, rectangle):
        self.completions_popover.set_size_request(rectangle.width, -1)

    def _on_user_added(self, _, user):
        if not user.deleted:
            completion = '@{}'.format(user.name)
            self._completions.append(completion)
            row = self._build_completion_row(completion)
            self.completions.add(row)
            self.completions.show_all()

    def _set_completions(self):
        self._completions = [
            *[
                '#{}'.format(channel.name)
                for channel in self._ws.channels
                if isinstance(channel, PublicChannel) and channel.is_open
            ],
            *[
                '@{}'.format(user.name)
                for user in self._ws.users
                if not user.deleted
            ],
            *[
                ':{}:'.format(emoji.name)
                for emoji in self._ws.emojis
            ]
        ]
        for row in self.completions.get_children():
            self.completions.remove(row)
        for completion in self._completions:
            row = self._build_completion_row(completion)
            self.completions.add(row)
        self.completions.show_all()

    def _show_completions(self):
        self.completions_popover.popup()
        self._completions_first()
