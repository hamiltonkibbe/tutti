#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Hamilton Kibbe <ham@hamiltonkib.be>

import hashlib
import inspect
import os
import sys

def get_name_from_caller():
    previous_frame = inspect.currentframe().f_back.f_back
    filename, line_no, function_name, lines, index = inspect.getframeinfo(previous_frame)
    relfilename = os.path.relpath(filename, sys.argv[0])
    hash_filename = filename.split("/")[-1] if relfilename == "." else relfilename
    to_hash = ",".join([hash_filename, str(line_no), function_name])
    return hashlib.sha256(to_hash.encode()).hexdigest()
