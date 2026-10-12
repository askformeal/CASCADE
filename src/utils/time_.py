from typing import Literal

from src.sentinels import SENTINELS, Sentinel

def format_time(
        raw_time: int | None,
        unit: Literal['ms', 'sec'] = 'ms',
        format_: Literal['colon', 'text'] = 'colon'
        ) -> str:

    if format_ == 'colon':
        empty = '--:--:--'
        zero = '00:00:00'
    
    elif format_ == 'text':
        empty = '-- seconds'
        zero = '0 seconds'

    if raw_time is None:
        return empty
    else:
        raw_time = round(float(raw_time))

        if raw_time == -1:
            return empty
        elif raw_time == 0:
            return zero

        if unit == 'sec':
            ms = raw_time * 1000
        else:
            ms = raw_time

        hours, remain = divmod(ms, 3600000) # 3600000 = 1000 * 60 * 60
        minutes, remain = divmod(remain, 60000) # 60000 = 1000 * 60
        seconds = remain // 1000

        if format_ == 'colon':
            return f'{hours:02}:{minutes:02}:{seconds:02}'
        elif format_ == 'text':
            text = f'{seconds} seconds'
            if minutes > 0:
                text = f'{minutes} minutes ' + text
            if hours > 0:
                text = f'{hours} hours ' + text
            return text
        
def parse_time(time: str) -> int | Sentinel:
    # Technically it can parse things like 999999:9999999:999999 but I decided to count that as a feature
    parts: list[str|int] = time.split(':')

    length = len(parts)
    if length > 3:
        return SENTINELS.INVALID_TIME
    else:
        for i in range(length):
            try:
                parts[i] = int(parts[i])
            except ValueError:
                return SENTINELS.INVALID_TIME
            else:
                if parts[i] < 0:
                    return SENTINELS.INVALID_TIME

        parts = [0, 0] + parts
        ms = parts[-1] * 1000 + parts[-2] * 60000 + parts[-3] * 3600000
        return ms