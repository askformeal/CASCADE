def process_request(args: dict) -> dict:
    action_translate = {
        'reload': 'load_last',
        'play-all': 'play_all',
        'reload-lyric': 'reload_lyric',
        'lyric': 'switch_lyric_mode'
    }
    args['action'] = action_translate.get(args['action'], args['action'])

    if args.get('meta_action', None) is not None:
        args['lib_action'] = f"{args['lib_action']}.{args['meta_action']}"
        del args['meta_action']

    if args.get('alias_action', None) is not None:
        args['lib_action'] = f"{args['lib_action']}.{args['alias_action']}"
        del args['alias_action']

    if args.get('lyric_action', None) is not None:
        args['lib_action'] = f"{args['lib_action']}.{args['lyric_action']}"
        del args['lyric_action']

    if args.get('playlist_action', None) is not None:
        args['lib_action'] = f"{args['lib_action']}.{args['playlist_action']}"
        del args['playlist_action']

    if args.get('lib_action', None) is not None:
        args['action'] = f"{args['action']}.{args['lib_action']}"
        del args['lib_action']

    if args.get('config_action', None) is not None:
        args['action'] = f"{args['action']}.{args['config_action']}"
        del args['config_action']

    return args