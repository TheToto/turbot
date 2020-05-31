#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#pylint: disable=C0103

"""
    Settings, argparser and logger
"""

import argparse
import logging

settings = None
logger = logging.getLogger(__name__)
output = logging.getLogger("output")

def arg_parse():
    """
        Parse the arguments and apply bits of the configuration given
    """
    global settings
    global logger

    parser = argparse.ArgumentParser()

    output_control = parser.add_mutually_exclusive_group()
    output_control.add_argument('-q', '--quiet', action='store_true', default=False,
                                help="Only print errors Léodagan found. Use for scripts")
    output_control.add_argument('--list-success', action='store_true', default=False,
                                help="Only output the list of people who passed the tests")
    output_control.add_argument('--list-fail', action='store_true', default=False,
                                help="Only output the list of people who did not passed the tests")

    parser.add_argument('-v', '--verbose', default=0, action='count', help="Increase verbosity")
    parser.add_argument('files', metavar='file', type=str, nargs='*',
                        help="files on which to run Léodagan")
    parser.add_argument('--process-all-files', action='store_true', default=False,
                        help="Should Léodagan process all files even if one does " + \
                             "not respect the nétiquette")
    parser.add_argument('--ignore-missing-file', action='store_true', default=False,
                        help="Should Léodagan ignore an unreadable or missing file")
    parser.add_argument('--extra-information', action='store_true', default=False,
                        help="Add extra information to provide better help")
    settings = parser.parse_args()

    console_handler = logging.StreamHandler()
    output_handler = logging.StreamHandler()
    lf = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')
    base_verbosity_console = 31
    base_verbosity_output = 31
    if settings.quiet:
        base_verbosity_console = 51
        lf = logging.Formatter('%(message)s')
    elif settings.list_success or settings.list_fail:
        base_verbosity_output = 51
        base_verbosity_console = 51
        lf = logging.Formatter('%(message)s')
    verbosity_threshold_console = base_verbosity_console - (settings.verbose * 10)
    verbosity_threshold_output = base_verbosity_output  - (settings.verbose * 10)
    console_handler.setLevel(verbosity_threshold_console)
    console_handler.setFormatter(lf)
    logger.addHandler(console_handler)
    logger.setLevel(verbosity_threshold_console)

    output_handler.setLevel(verbosity_threshold_output)
    output_handler.setFormatter(lf)
    output.addHandler(output_handler)
    output.setLevel(verbosity_threshold_output)
