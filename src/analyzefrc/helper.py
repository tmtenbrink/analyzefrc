import pathlib as path
import time


__all__ = ['create_save']


def create_save(folder_path: str = './results/', folder_name: str = 'frc_plots', add_timestamp=True):
    folder_path = folder_path.replace('\\', '/').removesuffix('/')
    if add_timestamp:
        timestamp = int(time.time())
        path_str = f"{folder_path}/{timestamp}-"
    else:
        path_str = f"{folder_path}/"
    path_result = path.Path(f"{path_str}{folder_name}")
    path_result.mkdir(parents=True, exist_ok=True)
    return path_result
