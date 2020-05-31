#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Represents all the exceptions
"""
# pylint: disable=missing-docstring

class Leodagan(Exception):
    type = "meta"
    def __init__(self, error, section):
        super().__init__()
        self.error = error
        self.section = section

    def __str__(self):
        return f"Invalid {self.type}: {self.error} / see {self.section}"

class Subject(Leodagan):
    type = "subject"

class Body(Leodagan):
    type = "message body"

class Signature(Leodagan):
    type = "signature"

class Quoting(Leodagan):
    type = "quoting"
