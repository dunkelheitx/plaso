# -*- coding: utf-8 -*-
"""Defines the output module for the SQLite database used by 4n6time."""

import os

import sqlite3

from plaso.output import manager
from plaso.output import shared_4n6time


class SQLite4n6TimeOutputModule(shared_4n6time.Base4n6TimeOutputModule):
  """Saves the data in a SQLite database, used by the tool 4n6time."""

  NAME = u'4n6time_sqlite'
  DESCRIPTION = (
      u'Saves the data in a SQLite database, used by the tool 4n6time.')

  _DEFAULT_FIELDS = frozenset([
      u'host', u'user', u'source', u'sourcetype', u'type', u'datetime',
      u'color'])

  _META_FIELDS = frozenset([
      u'sourcetype', u'source', u'user', u'host', u'MACB', u'color', u'type',
      u'record_number'])

  _CREATE_TABLE_QUERY = (
      u'CREATE TABLE log2timeline (timezone TEXT, '
      u'MACB TEXT, source TEXT, sourcetype TEXT, type TEXT, '
      u'user TEXT, host TEXT, description TEXT, filename TEXT, '
      u'inode TEXT, notes TEXT, format TEXT, extra TEXT, '
      u'datetime datetime, reportnotes TEXT, '
      u'inreport TEXT, tag TEXT, color TEXT, offset INT,'
      u'store_number INT, store_index INT, vss_store_number INT,'
      u'url TEXT, record_number TEXT, event_identifier TEXT, '
      u'event_type TEXT, source_name TEXT, user_sid TEXT, '
      u'computer_name TEXT, evidence TEXT)')

  _INSERT_QUERY = (
      u'INSERT INTO log2timeline(timezone, MACB, source, '
      u'sourcetype, type, user, host, description, filename, '
      u'inode, notes, format, extra, datetime, reportnotes, inreport,'
      u'tag, color, offset, store_number, store_index, vss_store_number,'
      u'URL, record_number, event_identifier, event_type,'
      u'source_name, user_sid, computer_name, evidence) '
      u'VALUES (:timezone, :MACB, :source, :sourcetype, :type, :user, :host, '
      u':description, :filename, :inode, :notes, :format, :extra, :datetime, '
      u':reportnotes, :inreport, '
      u':tag, :color, :offset, :store_number, :store_index, '
      u':vss_store_number,'
      u':URL, :record_number, :event_identifier, :event_type,'
      u':source_name, :user_sid, :computer_name, :evidence)')

  def __init__(self, output_mediator, filename=None, **kwargs):
    """Initializes the output module object.

    Args:
      output_mediator: The output mediator object (instance of OutputMediator).
      filename: The filename.

    Raises:
      ValueError: if the file handle is missing.
    """
    if not filename:
      raise ValueError(u'Missing filename.')

    super(SQLite4n6TimeOutputModule, self).__init__(output_mediator, **kwargs)
    self._append = self._output_mediator.GetConfigurationValue(
        u'append', default_value=False)

    self._connection = None
    self._cursor = None

    self._evidence = self._output_mediator.GetConfigurationValue(
        u'evidence', default_value=u'-')
    self._fields = self._output_mediator.GetConfigurationValue(
        u'fields', default_value=self._DEFAULT_FIELDS)

    self._filename = filename
    self._set_status = self._output_mediator.GetConfigurationValue(
        u'set_status')

  def _GetDistinctValues(self, field_name):
    """Query database for unique field types.

    Args:
      field_name: name of the filed to retrieve.
    """
    self._cursor.execute(
        u'SELECT {0:s}, COUNT({0:s}) FROM log2timeline GROUP BY {0:s}'.format(
            field_name))

    result = {}
    row = self._cursor.fetchone()
    while row:
      if row[0]:
        result[row[0]] = row[1]
      row = self._cursor.fetchone()
    return result

  def _ListTags(self):
    """Query database for unique tag types."""
    all_tags = []
    self._cursor.execute(u'SELECT DISTINCT tag FROM log2timeline')

    # This cleans up the messy SQL return.
    tag_row = self._cursor.fetchone()
    while tag_row:
      tag_string = tag_row[0]
      if tag_string:
        tags = tag_string.split(u',')
        for tag in tags:
          if tag not in all_tags:
            all_tags.append(tag)
      tag_row = self._cursor.fetchone()
    # TODO: make this method an iterator.
    return all_tags

  def Close(self):
    """Disconnects from the database.

    This method will create the necessary indices and commit outstanding
    transactions before disconnecting.
    """
    # Build up indices for the fields specified in the args.
    # It will commit the inserts automatically before creating index.
    if not self._append:
      for field_name in self._fields:
        query = u'CREATE INDEX {0:s}_idx ON log2timeline ({0:s})'.format(
            field_name)
        self._cursor.execute(query)
        if self._set_status:
          self._set_status(u'Created index: {0:s}'.format(field_name))

    # Get meta info and save into their tables.
    if self._set_status:
      self._set_status(u'Creating metadata...')

    for field in self._META_FIELDS:
      values = self._GetDistinctValues(field)
      self._cursor.execute(u'DELETE FROM l2t_{0:s}s'.format(field))
      for name, frequency in iter(values.items()):
        self._cursor.execute((
            u'INSERT INTO l2t_{0:s}s ({1:s}s, frequency) '
            u'VALUES("{2:s}", {3:d}) ').format(field, field, name, frequency))
    self._cursor.execute(u'DELETE FROM l2t_tags')
    for tag in self._ListTags():
      self._cursor.execute(u'INSERT INTO l2t_tags (tag) VALUES (?)', [tag])

    if self._set_status:
      self._set_status(u'Database created.')

    self._connection.commit()
    self._cursor.close()
    self._connection.close()

    self._cursor = None
    self._connection = None

  def Open(self):
    """Connects to the database and creates the required tables.

    Raises:
      IOError: if a file with filename already exists.
    """
    if not self._append and os.path.isfile(self._filename):
      raise IOError((
          u'Unable to use an already existing file for output '
          u'[{0:s}]').format(self._filename))

    self._connection = sqlite3.connect(self._filename)
    self._cursor = self._connection.cursor()

    # Create table in database.
    if not self._append:
      self._cursor.execute(self._CREATE_TABLE_QUERY)

      for field in self._META_FIELDS:
        query = u'CREATE TABLE l2t_{0:s}s ({0:s}s TEXT, frequency INT)'.format(
            field)
        self._cursor.execute(query)
        if self._set_status:
          self._set_status(u'Created table: l2t_{0:s}'.format(field))

      self._cursor.execute(u'CREATE TABLE l2t_tags (tag TEXT)')
      if self._set_status:
        self._set_status(u'Created table: l2t_tags')

      query = u'CREATE TABLE l2t_saved_query (name TEXT, query TEXT)'
      self._cursor.execute(query)
      if self._set_status:
        self._set_status(u'Created table: l2t_saved_query')

      query = (
          u'CREATE TABLE l2t_disk (disk_type INT, mount_path TEXT, '
          u'dd_path TEXT, dd_offset TEXT, storage_file TEXT, export_path TEXT)')
      self._cursor.execute(query)

      query = (
          u'INSERT INTO l2t_disk (disk_type, mount_path, dd_path, dd_offset, '
          u'storage_file, export_path) VALUES (0, "", "", "", "", "")')
      self._cursor.execute(query)
      if self._set_status:
        self._set_status(u'Created table: l2t_disk')

    self.count = 0

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
                        type in the event object.
    """
    if u'timestamp' not in event_object.GetAttributes():
      return

    row = self._GetSanitizedEventValues(event_object)
    self._cursor.execute(self._INSERT_QUERY, row)
    self.count += 1
    # Commit the current transaction every 10000 inserts.
    if self.count % 10000 == 0:
      self._connection.commit()
      if self._set_status:
        self._set_status(u'Inserting event: {0:d}'.format(self.count))


manager.OutputManager.RegisterOutput(SQLite4n6TimeOutputModule)
