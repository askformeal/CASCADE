class Response:
    def __init__(self, msg=None, code=None, attachment=None, failed=None):
        if code is None:
            self.code = 3
        else:
            self.code = code

        if msg is None:
            self.msg = 'undefined message'
        else:
            self.msg = msg

        if attachment is None:
            self.attachment = {}
        else:
            self.attachment = attachment

        if failed is None:
            self.failed = []
        else:
            self.failed = failed

        self.notifies = []

    def __repr__(self):
        return str(dict(self))

    def keys(self):
        return vars(self).keys()

    def __getitem__(self, key):
        # this is for dict(). do not access attr with [], use the dot.
        return getattr(self, key)

    def __add__(self, other):
        return merge(self, other)

    def __iadd__(self, other):
        self.append(other)
        return self
    
    def ok(self):
        return self.code == 0
    
    def append(self, *responses, **kwargs):
        result = merge(self, *responses, **kwargs)
        
        self.code = result.code
        self.msg = result.msg
        if result.attachment != {}:
            self.attachment = result.attachment

        if result.failed != []:
            self.failed = result.failed

class Success(Response):
    def __init__(self, msg=None, attachment=None, failed=None):
        super().__init__(msg, 0, attachment, failed)

class Failed(Response):
    def __init__(self, msg=None, attachment=None, failed=None):
        super().__init__(msg, 1, attachment, failed)

class BatchAuto(Response):
    def __init__(self, action, failed_num, total_num, attachment=None, failed=None):
        if failed_num < total_num:
            code = 0
        else:
            code = 1

        super().__init__(f'{action} [{total_num-failed_num}/{total_num}]', code, attachment, failed)

class Dying(Response):
    def __init__(self):
        super().__init__('backend is dying', code=4)

class Undefined(Response):
    def __init__(self):
        super().__init__('undefined response', code=3)

class AuthFailed(Response):
    def __init__(self):
        super().__init__('authorization failed', code=5)

class UnknownAction(Failed):
    def __init__(self, action, attachment=None, failed=None):
        super().__init__(f'unknown action received: \"{action}\"', attachment, failed)

class InvalidPath(Failed):
    def __init__(self, path, attachment=None, failed=None):
        super().__init__(f'\"{path}\" can not be parsed as a valid and existing path', attachment, failed)

class SongNotExist(Failed):
    def __init__(self, song, attachment=None, failed=None):
        super().__init__(f'no such song in library: {song}', attachment, failed)
    
class PlaylistNotExist(Failed):
    def __init__(self, playlist, attachment=None, failed=None):
        super().__init__(f'no such playlist in library: {playlist}', attachment, failed)

class MissingKey(Failed):
    def __init__(self, key, attachment=None, failed=None):
        super().__init__(f'key not received: {key}', attachment, failed)

class MissingCWD(Failed):
    def __init__(self, attachment=None, failed=None):
        super().__init__(f'one or more paths provided are not absolute paths but the \"cwd\" key is not provided', attachment, failed)

class InvalidKeyType(Failed):
    def __init__(self, key, value, error, attachment=None, failed=None):
        super().__init__(f'invalid value \"{value}\" of key \"{key}\": {error}', attachment, failed)

class EmptyList(Failed):
    def __init__(self, item, attachment=None, failed=None):
        super().__init__(f'received empty list of {item}', attachment, failed)

class PercentageTooLow(Failed):
    def __init__(self, value, attachment=None, failed=None):
        super().__init__(f'lower than 0 percentage: {value}', attachment, failed)

class PercentageTooHigh(Failed):
    def __init__(self, value, attachment=None, failed=None):
        super().__init__(f'higher than 100 percentage: {value}', attachment, failed)

class PlayerEmpty(Failed):
    def __init__(self, attachment=None, failed=None):
        super().__init__(f'no songs are being played', attachment, failed)

class NotPlayingPaused(Failed):
    def __init__(self, attachment=None, failed=None):
        super().__init__(f'the player is neither playing nor paused', attachment, failed)

class InvalidAudioFile(Failed):
    def __init__(self, attachment=None, failed=None):
        super().__init__(f'audio file not exist or invalid', attachment, failed)

class EngineError(Failed):
    def __init__(self, attachment=None, failed=None):
        super().__init__(f'an internal audio engine error occurred', attachment, failed)

class PlayerTimeout(Failed):
    def __init__(self, attachment=None, failed=None):
        super().__init__(f'timed out waiting for player to complete the action', attachment, failed)

class PosTooLate(Failed):
    def __init__(self, pos, attachment=None, failed=None):
        super().__init__(f'tried to jump to a position later than the end of the song: {pos}', attachment, failed)

class OptionNotExist(Failed):
    def __init__(self, attachment=None, failed=None):
        super().__init__(f'option does not exist', attachment, failed)

class LyricNotExist(Failed):
    def __init__(self, attachment=None, failed=None):
        super().__init__('no lyric file set for the song', attachment, failed)

class FileIOFailed(Failed):
    def __init__(self, path, error=None, attachment=None, failed=None):
        msg = f'failed to read / write \"{path}\"'
        if error is not None:
            msg += f': {error}'
        super().__init__(msg, attachment, failed)

class DatabaseError(Failed):
    def __init__(self, attachment=None, failed=None):
        super().__init__('a database error occurred', attachment, failed)

def merge(*responses: Response, joiner='|', attachment=None, failed=None):
    messages = []
    codes = []

    for response in responses:
        if response is not None:
            messages.append(response.msg)
            codes.append(response.code)

    if len(codes) > 0:
        msg = f' {joiner} '.join(messages)
        code = max(codes)
        return Response(msg, code, attachment=attachment, failed=failed)
    else:
        return Response('', attachment=attachment, failed=failed)