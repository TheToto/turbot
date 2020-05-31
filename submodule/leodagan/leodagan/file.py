#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Get the input from file(s)
"""

import leodagan.settings as ls
import leodagan.engine as lengine

def run_files(files: list):
    """
        Run léodagan on the given files
    """
    for file_ in files:
        ls.logger.debug(f"Will treat file {file_}")
        try:
            with open(file_, "r") as f:
                content = f.read()
        except (FileNotFoundError, PermissionError, UnicodeDecodeError, IsADirectoryError):
            if ls.settings.ignore_missing_file:
                ls.logger.warning(f"Unreadable file : {file_} ... skipping")
                continue
            ls.logger.error(f"Unreadable file : {file_} ... aborting")
            return False

        is_content_compliant = lengine.process_news(content, identification=file_)

        if not is_content_compliant and ls.settings.process_all_files:
            ls.logger.warning(f"File {file_} does not respect the nétiquette !")
        elif not is_content_compliant:
            ls.logger.error(f"File {file_} does not respect the nétiquette !")
            return False
        else:
            ls.logger.info(f"File {file_} is nétiquette compliant")
    return True
