from PyQt5 import QtWidgets


class MyWidget(QtWidgets.QLabel):
    @classmethod
    def get_designer_info(cls):
        return dict(
            is_container=False,
            group='Example project group',
            extensions=None,
            icon=None,
        )

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setText('My Widget')


def form_added_hook(form):
    print('Hi from the example. A form was added:', form)
