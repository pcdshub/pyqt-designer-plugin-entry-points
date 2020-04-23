import entrypoints


def get_entrypoint_object(entry_name, item):
    class EntrypointStubObject:
        name = entry_name

        def load(self):
            if isinstance(item, Exception):
                raise item
            return item

        def __repr__(self):
            return f'<EntrypointStubObject name={self.name} item={item}>'

    return EntrypointStubObject()


def patch_entrypoint(monkeypatch, object_dict):
    def get_group_all(key):
        for name, obj in object_dict.get(key, {}).items():
            yield get_entrypoint_object(name, obj)

    monkeypatch.setattr(entrypoints, 'get_group_all', get_group_all)
