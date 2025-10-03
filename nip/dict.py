from .utils import iterate_items


class DictObject(dict):
    def __init__(self, obj):
        d = {}
        if isinstance(obj, (list, dict)):
            for key, value in iterate_items(obj):
                d[key] = value
                if isinstance(value, (tuple, list, dict)):
                    d[key] = DictObject(value)

        elif isinstance(obj, tuple):
            for key, value in iterate_items(obj[0]):
                d[key] = value
                if isinstance(value, (tuple, list, dict)):
                    d[key] = DictObject(value)
            for key, value in iterate_items(obj[1]):
                d[key] = value
                if isinstance(value, (tuple, list, dict)):
                    d[key] = DictObject(value)
        else:
            raise ValueError("Expected Iterable type for Converting to DictObject")
        super(DictObject, self).__init__(**d)

    def __getattr__(self, item):
        return self[item]
