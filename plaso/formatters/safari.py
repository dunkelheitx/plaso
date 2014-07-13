#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Formatter for the Safari History events."""

from plaso.formatters import interface


class SafariHistoryFormatter(interface.ConditionalEventFormatter):
  """Formatter for Safari history events."""

  DATA_TYPE = 'safari:history:visit'

  FORMAT_STRING_PIECES = [
      u'Visited: {url}', u'({title}', u'- {display_title}', ')',
      'Visit Count: {visit_count}']

  SOURCE_LONG = 'Safari History'
  SOURCE_SHORT = 'WEBHIST'
