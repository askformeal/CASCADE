from pystray import MenuItem

class Label(MenuItem):
    def __init__(self, text: str):
        super().__init__(text, None, enabled=False)