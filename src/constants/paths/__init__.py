from pathlib import Path
from platformdirs import PlatformDirs

dirs = PlatformDirs('cascade', ensure_exists=True)

DATA_DIR = Path(dirs.user_data_dir)
CONFIG_DIR = Path(dirs.user_config_dir)

DATABASE = DATA_DIR / 'cascade.db'
DATABASE_DEV = DATA_DIR / 'cascade-dev.db'

PID_PATH = DATA_DIR / 'PID.json'
CONFIG_PATH = CONFIG_DIR / 'config.toml'
