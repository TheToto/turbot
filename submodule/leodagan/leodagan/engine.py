#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    The engine part making the link between the input and the rules
"""

import sys
from email.header import decode_header
import leodagan.rules as lr
import leodagan.exceptions as le
import leodagan.settings as ls

class News():
    """
        Represent a news
    """

    @staticmethod
    def parse_headers(lines: list) -> dict:
        """
            Parse the headers of a news
        """
        headers = {}

        for i in range(len(lines)):
            line = lines[i]
            if line == '': # end of headers
                break
            if line[0] == ' ' or line[0] == '\t': # Multiline headers already handled
                continue
            header = line.split(": ", 1)

            if len(header) == 1:
                headers[header[0].lower()] = ""
                continue

            # Handle multiline headers
            peek = 1
            while True: # Do while
                try:
                    if lines[i + peek][0] == ' ':
                        header[1] += ' ' + lines[i + peek]
                        peek += 1
                    else:
                        break
                except IndexError:
                    break

            # Handle values like =?UTF-8?Q?=5bINFRA=5d=5bMAINTENANCE=5d_Coupure?=
            decoded_el = decode_header(header[1])
            value = ""
            for el in decoded_el:
                if el[1] is None and isinstance(el[0], str): # No encoding used
                    value += el[0]
                elif el[1] is not None: # Decode using given encoding
                    value += el[0].decode(el[1], errors='ignore')
                else:
                    value += el[0].decode('utf-8', errors='ignore')
            headers[header[0].lower()] = value
        return headers

    def __init__(self, content):
        self.content = content
        self.lines = content.split("\n")
        self.headers = News.parse_headers(self.lines)
        self.body = content[content.find("\n\n") + 2:]

    def __str__(self):
        return str(self.headers) + "\n\n" + self.body

def check_wrapper(func, *args):
    """
        A wrapper of checker to catch the exceptions
    """
    try:
        func(*args)
        ls.logger.debug(f"{func} checked")
        return False
    except le.Leodagan as err:
        ls.output.error(f"Léodagan: {str(err)}")
        return True

def check_wrapper_iter(func, *args):
    """
        A wrapper of checker to iter of rule-generator
    """
    ret_code = False
    gen = iter(func(*args))
    try:
        while True:
            try:
                obj = gen.__next__()
                if obj is not None:
                    raise obj
            except le.Leodagan as err:
                ls.output.error(f"Léodagan: {str(err)}")
                ret_code = True
    except StopIteration:
        return ret_code

def process_news(content: str, identification: str = None):
    """
        Process a news with its content and apply the rules
    """
    try:
        news = News(content)
    except Exception as err: # FIXME
        ls.logger.error(f"Cannot parse content : {str(err)}")
        return False

    error_found = False

    error_found |= check_wrapper_iter(lr.check_subject, news.headers.get("subject"))
    error_found |= check_wrapper(lr.check_basic_body_formatting, news.body)
    error_found |= check_wrapper_iter(lr.check_max_cols, news.body)
    error_found |= check_wrapper(lr.check_signature, news.body)
    error_found |= check_wrapper(lr.check_quoting, news.body)

    if (ls.settings.list_success and not error_found) or (ls.settings.list_fail and error_found):
        user_from = news.headers.get("from", None)
        if user_from is None:
            print(f"Could not get author from news {identification}", file=sys.stderr)
        elif ls.settings.verbose > 0:
            print(f'{user_from} / {identification}')
        else:
            print(user_from)

    return not error_found
