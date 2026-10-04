from src.types import CONVERTER

REPO_LINK = 'https://github.com/askformeal/CASCADE'

ENCODING = 'utf-8'
ENCODING_CHAIN = ('utf-8', 'gb18030', 'big5', 'shift_jis', 'utf-16')

READABLE_TYPE_NAMES = {
    str: 'string',
    int: 'integer',
    bool: 'boolean',
    CONVERTER.boolean: 'boolean',
    CONVERTER.port: 'network port',
    CONVERTER.pos_int: 'positive integer',
    CONVERTER.non_neg_int: 'non-negative integer',
    CONVERTER.timeout: 'positive float',
    CONVERTER.percentage: 'percentage number',
    CONVERTER.hex_color: 'hex color',
}

TYPE_CODENAMES = {
    str: 'str',
    int: 'int',
    bool: 'bool',
    CONVERTER.boolean: 'bool',
    CONVERTER.port: 'port',
    CONVERTER.pos_int: 'pos_int',
    CONVERTER.non_neg_int: 'no_neg_integer',
    CONVERTER.timeout: 'pos_float',
    CONVERTER.percentage: 'percent',
    CONVERTER.hex_color: 'hex_color',
}

MIN_TIMEOUT = 0.01

WINDOWS_ILLEGAL = r'[<>:"|?*]'
WINDOWS_RESERVED = {'CON', 'PRN', 'AUX', 'NUL',
                    'COM1','COM2','COM3','COM4','COM5','COM6','COM7','COM8','COM9',
                    'LPT1','LPT2','LPT3','LPT4','LPT5','LPT6','LPT7','LPT8','LPT9'}

BOX_STYLES = {
    'invisible': (' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '),
    'ascii': ('/', '\\', '\\', '/', '|', '=', '+', '+'),
    'at': ('@', '@', '@', '@', '|', '=', '+', '+'),
    'rounded': ('╭', '╮', '╰', '╯', '│', '─', '┬', '┴'),
    'square': ('┌', '┐', '└', '┘', '│', '─', '┬', '┴'),
    'double-corner': ('╔', '╗', '╚', '╝', '│', '─', '┬', '┴'),
    'heavy-corner': ('┏', '┓', '┗', '┛', '│', '─', '┬', '┴'),
    'double': ('╔', '╗', '╚', '╝', '║', '═', '╦', '╩'),
    'heavy': ('┏', '┓', '┗', '┛', '┃', '━', '┳', '┻'),
}

# file type descriptions, kept short like those used in file selectors
AUDIO_FILE_TYPES = (
    ('MP3 Audio', '.mp3'),
    ('FLAC Audio', '.flac'),
    ('WAV Audio', '.wav'),
    ('OGG Audio', '.ogg'),
    ('Opus Audio', '.opus'),
    ('OGG Audio', '.oga'),
    ('M4A Audio', '.m4a'),
    ('M4B Audio', '.m4b'),
    ('AAC Audio', '.aac'),
    ('MP4 Audio', '.mp4'),
    ('M4P Audio', '.m4p'),
    ('APE Audio', '.ape'),
    ('WMA Audio', '.wma'),
    ('AIFF Audio', '.aiff'),
    ('AIF Audio', '.aif'),
    ('AU Audio', '.au'),
    ('AC3 Audio', '.ac3'),
    ('DTS Audio', '.dts'),
    ('DSF Audio', '.dsf'),
    ('DSD Audio', '.dsd'),
    ('DFF Audio', '.dff'),
    ('MKA Audio', '.mka'),
    ('WV Audio', '.wv'),
    ('MPC Audio', '.mpc'),
    ('TTA Audio', '.tta'),
    ('TAK Audio', '.tak'),
    ('RA Audio', '.ra'),
    ('RM Audio', '.rm'),
    ('AMR Audio', '.amr'),
    ('3GP Audio', '.3gp'),
    ('CAF Audio', '.caf'),
    ('MIDI Audio', '.mid'),
    ('MIDI Audio', '.midi'),
    ('Speex Audio', '.spx'),
)

AUDIO_EXTENSIONS = set(map(lambda x: x[1], AUDIO_FILE_TYPES))

IMAGE_FILE_TYPES = (
    ('PNG Image', '*.png'),
    ('APNG Image', '*.apng'),
    ('JPEG Image', '*.jpg'),
    ('JPEG Image', '*.jpeg'),
    ('JPEG Image', '*.jpe'),
    ('JPEG Image', '*.jfif'),
    ('WebP Image', '*.webp'),
    ('GIF Image', '*.gif'),
    ('BMP Image', '*.bmp'),
    ('TIFF Image', '*.tif'),
    ('TIFF Image', '*.tiff'),
    ('ICO Image', '*.ico'),
    ('AVIF Image', '*.avif'),
    ('AVIF Image', '*.avifs'),
    ('QOI Image', '*.qoi'),
    ('JPEG 2000 Image', '*.jp2'),
    ('JPEG 2000 Image', '*.j2k'),
    ('JPEG 2000 Image', '*.j2c'),
    ('JPEG 2000 Image', '*.jpc'),
    ('JPEG 2000 Image', '*.jpf'),
    ('JPEG 2000 Image', '*.jpx'),
    ('TGA Image', '*.tga'),
    ('TGA Image', '*.icb'),
    ('TGA Image', '*.vda'),
    ('TGA Image', '*.vst'),
    ('PCX Image', '*.pcx'),
    ('DDS Image', '*.dds'),
    ('ICNS Image', '*.icns'),
    ('DIB Image', '*.dib'),
    ('IM Image', '*.im'),
    ('MPO Image', '*.mpo'),
    ('BLP Image', '*.blp'),
    ('MSP Image', '*.msp'),
    ('PALM Image', '*.palm'),
    ('XBM Image', '*.xbm'),
    ('PPM Image', '*.ppm'),
    ('PPM Image', '*.pgm'),
    ('PPM Image', '*.pbm'),
    ('PPM Image', '*.pnm'),
    ('PPM Image', '*.pfm'),
    ('SGI Image', '*.sgi'),
    ('SGI Image', '*.rgb'),
    ('SGI Image', '*.rgba'),
    ('SGI Image', '*.bw'),
    ('PDF Document', '*.pdf'),
    ('EPS Document', '*.eps'),
    ('EPS Document', '*.ps'),
)
