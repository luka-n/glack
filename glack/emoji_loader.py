import json
import os

from gi.repository import GLib, GdkPixbuf, Gio, Soup


class EmojiLoader:
    def __init__(self):
        self.emoji_data_dir = os.environ['GLACK_EMOJI_DATA_DIR']
        self._ensure_cache_dir()
        self._soup = Soup.SessionAsync()
        self.emoji = {}
        self._load_data()
        self._load_custom()

    def add_custom(self, name, url, callback):
        path = os.path.join(self.emoji_cache_dir, name)
        if not GLib.file_test(path, GLib.FileTest.EXISTS):
            message = Soup.Message.new('GET', url)

            def finish(session, message):
                custom_file = Gio.File.new_for_path(path)
                outstream = custom_file.replace(
                    None, False, Gio.FileCreateFlags.NONE, None
                )
                outstream.write_bytes(
                    message.response_body.flatten().get_as_bytes(),
                    None
                )
                self.emoji[name] = path
                callback(name, path)
            self._soup.queue_message(message, finish)

    def get_pixbuf(self, name, size=64):
        if name not in self.emoji:
            return None
        path = self.emoji[name]
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
        if size != 64:
            pixbuf = pixbuf.scale_simple(
                size, size, GdkPixbuf.InterpType.BILINEAR
            )
        pixbuf._name = name
        return pixbuf

    def _ensure_cache_dir(self):
        self.emoji_cache_dir = os.path.join(
            GLib.get_user_cache_dir(), 'glack', 'emoji'
        )
        if not GLib.file_test(self.emoji_cache_dir, GLib.FileTest.IS_DIR):
            cache_dir = Gio.File.new_for_path(self.emoji_cache_dir)
            cache_dir.make_directory_with_parents()

    def _load_custom(self):
        for file_name in os.listdir(self.emoji_cache_dir):
            self.emoji[file_name] = \
                os.path.join(self.emoji_cache_dir, file_name)

    def _load_data(self):
        path = os.path.join(self.emoji_data_dir, 'emoji.json')
        json_file = Gio.File.new_for_path(path)
        file_data = json_file.load_contents()[1]
        data = json.loads(file_data)
        for item in data:
            if item['has_img_google']:
                self.emoji[item['short_name']] = os.path.join(
                    self.emoji_data_dir, 'img-google-64', item['image']
                )
