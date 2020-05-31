#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import leodagan.settings as ls
import leodagan.engine as lengine

def read_input():
    ls.logger.debug("Reading from stdin")
    input_msg = sys.stdin.read()
    ls.logger.debug(f"Read {len(input_msg)} chars from stdin")

    is_content_compliant = lengine.process_news(input_msg, identification="stdin")

    if not is_content_compliant:
        ls.logger.error(f"Input does not respect the nétiquette !")
    else:
        ls.logger.info(f"Input is nétiquette compliant")

    return is_content_compliant
