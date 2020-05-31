#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Léodagan, a nétiquette checker for EPITA
    https://gitlab.cri.epita.fr/cyril/leodagan
"""

import leodagan.settings as ls
import leodagan.file as lf
import leodagan.stdin as lin

def main():
    # pylint: disable=missing-docstring
    ls.arg_parse()
    if ls.settings.files:
        if lf.run_files(ls.settings.files):
            exit(0)
        exit(1)
    else:
        lin.read_input()

if __name__ == "__main__":
    main()
