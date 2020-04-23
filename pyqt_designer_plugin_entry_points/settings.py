import sys

from . import core


def list_widgets(file=sys.stdout):
    print(file=file)
    print('Widgets', file=file)
    print('-------', file=file)
    for name, wrapped_cls in core.enumerate_widgets().items():
        cls = wrapped_cls.info()['cls']
        print(f'{name} ({cls.__module__}.{cls.__name__})', file=file)


def list_connections(file=sys.stdout):
    print(file=file)
    print('Events hooked', file=file)
    print('-------------', file=file)
    for name, (event, func) in core.enumerate_all_events():
        print(f'{name}: {event.module_name}.{event.object_name} {func}',
              file=file)


def main(file=sys.stdout):
    list_widgets(file=file)
    list_connections(file=file)


if __name__ == '__main__':
    main()
