from importlib.resources import files

def get_res(filename):
    return str(files('res') / filename)

LICENSE = get_res('license.txt')

ICON = get_res('icon.ico')
ERROR_ICON = get_res('icon_error.ico')
LYRIC_ICON = get_res('lyric_icon.ico')
NO_COVER = get_res('no_cover.txt')
