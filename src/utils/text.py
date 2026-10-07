import re

from wcwidth import wcswidth

ESCAPE_PATTERN = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')

def strlen(text):
    text = ESCAPE_PATTERN.sub('', text)
    visible_text = ''
    for char in text:
        if char.isprintable():
            visible_text += char
    return wcswidth(visible_text)

def wrap_text(text, max_len):
    lines = []
    line = ''
    words = text.split(' ')
    for word in words:
        if strlen(line) + strlen(word) + 1 <= max_len:
            if line != '':
                line += ' '
            line += word
        else:
            lines.append(line)
            line = word
            while strlen(line) > max_len:
                cut_text = ''
                while strlen(cut_text) < max_len:
                    cut_text += line[0]
                    line = line[1:]
                lines.append(cut_text)
    
    lines.append(line)
    
    while '' in lines:
        lines.remove('')
    
    return '\n'.join(lines)
