from gi.repository import GObject

from glack.models.avatar import Avatar


class User(GObject.GObject):
    avatar = GObject.Property(type=Avatar)
    deleted = GObject.Property(type=bool, default=False)
    id = GObject.Property(type=str)
    name = GObject.Property(type=str)
    presence = GObject.Property(type=str)
    title = GObject.Property(type=str)
    username = GObject.Property(type=str)

    def __init__(self, ws, data):
        super().__init__()
        self._ws = ws
        self.id = data['id']
        self.set_from_data(data)

    def set_from_data(self, data):
        profile = data['profile']
        if 'display_name' in profile and profile['display_name']:
            name = data['profile']['display_name']
        elif 'real_name' in data['profile'] and data['profile']['real_name']:
            name = data['profile']['real_name']
        else:
            name = data['name']

        new_data = {
            'avatar': Avatar(profile['avatar_hash'], profile['image_512']),
            'deleted': data['deleted'],
            'name': name,
            'username': data['name'],
            'presence': data['presence'] if 'presence' in data else None,
            'title': data['title'] if 'title' in data else None
        }

        for prop, new_value in new_data.items():
            old_value = self.get_property(prop)
            if new_value != old_value:
                self.set_property(prop, new_value)
