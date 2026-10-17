from types import NotImplementedType

class Empty:
    def __init__(self, msg: str = '[EMPTY]'):
        self.msg = msg

    def __repr__(self):
        return self.msg
    
    def __eq__(self, value) -> bool | NotImplementedType:
        if not isinstance(value, Empty):
            return NotImplemented
        else:
            return self is value

    def __hash__(self) -> int:
        return id(self)

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self
