# Copyright (C) 2021                Department of Imaging Physics
# All rights reserved               Faculty of Applied Sciences
#                                   TU Delft
# Tip ten Brink

import pathlib as path
from pathlib import Path
import time


__all__ = ['create_save']


def create_save(folder_path: str = './results/', folder_name: str = 'frc_plots', add_timestamp=True) -> Path:
    """
    Create a folder and add optional timestamp to prevent overwriting data.

    :param str folder_path: Parent path at which the folder will be created.
    :param str folder_name: Name of the folder that will be created.
    :param bool add_timestamp: Prepend a timestamp to the created folder.
    """
    folder_path = folder_path.replace('\\', '/').removesuffix('/')
    if add_timestamp:
        timestamp = int(time.time())
        path_str = f"{folder_path}/{timestamp}-"
    else:
        path_str = f"{folder_path}/"
    path_result = path.Path(f"{path_str}{folder_name}")
    path_result.mkdir(parents=True, exist_ok=True)
    return path_result
