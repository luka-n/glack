from gi.repository import GdkPixbuf, Soup


class UrlPreview:
    @staticmethod
    def new_from_url(url, callback):
        soup = Soup.SessionAsync()

        def handle_get(_session, message):
            content_type, _ = message.response_headers.get_content_type()
            data = message.response_body.flatten().get_as_bytes()
            if content_type in ImageUrlPreview.get_formats():
                callback(ImageUrlPreview(data))

        def handle_head(_session, message):
            content_length = message.response_headers.get_content_length()
            content_length_mb = content_length / 1000 / 1000
            if content_length_mb <= 2:
                message = Soup.Message.new('GET', url)
                soup.queue_message(message, handle_get)

        message = Soup.Message.new('HEAD', url)
        soup.queue_message(message, handle_head)


class ImageUrlPreview(UrlPreview):
    @staticmethod
    def get_formats():
        return [
            i for sub in [
                f.get_mime_types() for f in GdkPixbuf.Pixbuf.get_formats()
            ] for i in sub
        ]

    def __init__(self, data):
        loader = GdkPixbuf.PixbufLoader.new()
        loader.write_bytes(data)
        loader.close()

        self.original_pixbuf = loader.get_pixbuf()

        w = self.original_pixbuf.get_width()
        h = self.original_pixbuf.get_height()
        scale_ratio = min(min(360, w) / w, min(360, h) / h)

        self.pixbuf = self.original_pixbuf.scale_simple(
            w * scale_ratio,
            h * scale_ratio,
            GdkPixbuf.InterpType.BILINEAR
        )
