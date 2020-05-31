#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#pylint: disable=line-too-long

"""
    The rules léodagan will try to enforce
"""

import re
from dataclasses import dataclass
import leodagan.exceptions
import leodagan.settings as ls


@dataclass
class RegexUtils:
    """
        Data class for regexes
    """
    VALID_SUBJECT = re.compile(r"^(?:Re: ?)?(?:\[[A-Z0-9-_+/]{1,10}\]){2} .*$")
    ONE_TAG = re.compile(r"^(?:Re: ?)?(?:\[[A-Z0-9-_+/]{1,10}\]){1}\s*[^\[\s].*$")
    TRAILING_WHITESPACE = re.compile(r"^(?!>|(-- )).*\s$")
    OVER_80_ALLOWED = re.compile(r"^(?:>+ )?\[[0-9]{1,3}\] \w{2,5}://.*$")

def check_subject(subject: str):
    """
        Enforce rules about the subject line
    """
    if subject is None or subject == "":
        yield leodagan.exceptions.Subject("Empty or undefined subject", "2.1.1")
        yield StopIteration()
    if len(subject) > 80:
        yield leodagan.exceptions.Subject("Length exceed 80 chars", "2.1.1.2")
    if subject[:4] == "Re: ":
        yield StopIteration()
    if not RegexUtils.VALID_SUBJECT.match(subject):
        yield leodagan.exceptions.Subject("Subject must have tags and a summary", "2.1.1")
    if ls.settings.extra_information:
        if RegexUtils.ONE_TAG.match(subject):
            yield leodagan.exceptions.Subject("Subject cannot have only one tag", "2.1.1")

def check_basic_body_formatting(body: str):
    """
        Enforce the rules about the basics of the body
    """
    if body is None or body == "":
        raise leodagan.exceptions.Body("Empty or undefined body", "2.2.1")
    body = body.split("\n")

    if len(body) < 8:
        raise leodagan.exceptions.Body(f"A valid message has a minimum of 7 lines, as it needs at least a greeting/salutation line, a body and a signature", "2.2.1")

    if not '-- ' in body:
        raise leodagan.exceptions.Body("No signature found", "2.3")
    if body.count("-- ") > 1:
        raise leodagan.exceptions.Body("Signature separation must be unique", "2.3")

    # Checking for trailing whitespace
    for i in range(len(body)):
        line = body[i]
        if RegexUtils.TRAILING_WHITESPACE.match(line):
            raise leodagan.exceptions.Body(f"Line {i} has a trailing whitespace and is not a (valid) signature delimiter", "2.2.2.5")

    # Check for the greeting line
    if body[0] == '' or body[1] != '':
        raise leodagan.exceptions.Body("No greeting line. Please note that an empty line must be inserted after the greeting line", "2.2.1.1")
    end_body = body.index("-- ")
    if end_body < 6 or body[end_body - 1] != '' or body[end_body - 2] == '' or body[end_body - 3] != '':
        raise leodagan.exceptions.Body("No salutation line found. Please note that empty lines must be inserted before and after the salutation line", "2.2.1.1")

def check_max_cols(body: str):
    """
        Enforce the rule about the max width of a line
    """
    body = body.split("\n")
    i = 0
    for line in body:
        i += 1
        if len(line) <= 72:
            continue
        elif RegexUtils.OVER_80_ALLOWED.match(line):
            continue
        elif len(line) > 80:
            yield leodagan.exceptions.Body(f"Line {i} width exceeding 80 chars", "2.2.2.1")
        elif not line[0] == '>':
            yield leodagan.exceptions.Body(f"Line {i} width exceeding 72 chars without quoting", "2.2.2.1")
    yield None

def check_signature(body: str):
    """
        Enforce rules about the signature
    """
    body = body.split("\n")
    signature = []
    body_len = len(body)
    for i in range(body_len):
        line = body[i]
        if line == "-- ":
            if i + 1 == body_len:
                raise leodagan.exceptions.Signature("Signature musn't be empty", "2.3")
            signature = body[i + 1:]
    if not signature:
        raise leodagan.exceptions.Signature("Signature not found", "2.3")
    if len(signature) > 4:
        raise leodagan.exceptions.Signature("Signature too long", "2.3")
    if signature[0] == "":
        raise leodagan.exceptions.Signature("Signature musn't start with an empty line", "2.3")

def check_quoting(body: str):
    """
        Enforce rules about quoting people
    """
    quote_attribution_found = False
    body = body.split("\n")
    quote_section = False
    section_i = 0

    for i in range(len(body)):
        line = body[i]
        if line == '-- ':
            break
        if line != '':
            section_i += 1
        else:
            section_i = 0

        # Quoting line
        if len(line) > 0 and line[0] == '>':
            if not quote_section and section_i > 2:
                raise leodagan.exceptions.Quoting(f"Quote section must be preceded by an empty line or an attribution line (line {i})", "2.2.3.2")
            quote_section = True

            # Quote attribution lookup
            if not quote_section and not quote_attribution_found:
                if i > 0 and body[i - 1] != '':
                    quote_attribution_found = True
                else:
                    raise leodagan.exceptions.Quoting(f"Quote section must be attributed (line {i})", "2.2.3.3")

            # Multiple quoting rules
            for j in range(len(line)):
                if line[j] == '>':
                    continue
                if line[j] == ' ':
                    if j + 1 < len(line) and line[j + 1] == '>':
                        raise leodagan.exceptions.Quoting(f"Quoting multiple times should use multiple `>' without spaces in between", "2.2.3.2")
                    break
                raise leodagan.exceptions.Quoting(f"Quoting needs a space between the last `>' and its content (line {i})", "2.2.3.2")

        elif len(line) != 0 and quote_section:
            raise leodagan.exceptions.Quoting(f"Quoting sections must be separated by empty lines (line {i})", "2.2.3.2")
        elif len(line) == 0:
            quote_section = False
