#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Hamilton Kibbe <ham@hamiltonkib.be>

from typing import NamedTuple


class RedisSemaphoreHandle(NamedTuple):
    name: str
    identifier: str
