import os

from gi.repository import Gio, GLib, Soup


class AvatarCache:
    def __init__(self):
        self._cache_dir = os.path.join(
            GLib.get_user_cache_dir(), 'glack', 'avatars'
        )
        if not GLib.file_test(self._cache_dir, GLib.FileTest.IS_DIR):
            Gio.File.new_for_path(self._cache_dir) \
                .make_directory_with_parents()
        self._soup = Soup.SessionAsync()

    def get(self, avatar_hash, avatar_url, callback):
        path = os.path.join(self._cache_dir, avatar_hash)
        if GLib.file_test(path, GLib.FileTest.EXISTS):
            callback(path)
        else:
            def finish(_session, message):
                path = self.store(
                    avatar_hash,
                    message.response_body.flatten().get_as_bytes()
                )
                callback(path)

            message = Soup.Message.new('GET', avatar_url)
            self._soup.queue_message(message, finish)

    def store(self, avatar_hash, avatar_bytes):
        path = os.path.join(self._cache_dir, avatar_hash)
        file_ = Gio.File.new_for_path(path)
        outstream = file_.replace(None, False, Gio.FileCreateFlags.NONE, None)
        outstream.write_bytes(avatar_bytes, None)
        return path
