class Empty:
    def __init__(self, msg='[EMPTY]'):
        self.msg = msg

    def __repr__(self):
        return self.msg
    
    def __eq__(self, value):
        if not isinstance(value, Empty):
            return NotImplemented
        else:
            return self is value

    def __hash__(self):
        return id(self)