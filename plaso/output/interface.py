# -*- coding: utf-8 -*-
"""This file contains the output module interface classes."""

from __future__ import unicode_literals

import abc

from plaso.lib import errors
from plaso.output import logger


class OutputModule(object):
  """Output module interface."""

  NAME = ''
  DESCRIPTION = ''

  def __init__(self, output_mediator):
    """Initializes an output module.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfvfs.
    """
    super(OutputModule, self).__init__()
    self._output_mediator = output_mediator

  def _ReportEventError(self, event, event_data, error_message):
    """Reports an event related error.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      error_message (str): error message.
    """
    event_identifier = event.GetIdentifier()
    event_identifier_string = event_identifier.CopyToString()
    display_name = getattr(event_data, 'display_name', None) or 'N/A'
    parser_chain = getattr(event_data, 'parser', None) or 'N/A'
    error_message = (
        'Event: {0!s} data type: {1:s} display name: {2:s} '
        'parser chain: {3:s} with error: {4:s}').format(
            event_identifier_string, event_data.data_type, display_name,
            parser_chain, error_message)
    logger.error(error_message)

  def Close(self):
    """Closes the output."""
    return

  def GetMissingArguments(self):
    """Retrieves arguments required by the module that have not been specified.

    Returns:
      list[str]: names of argument that are required by the module and have
          not been specified.
    """
    return []

  def Open(self):
    """Opens the output."""
    return

  def WriteEvent(self, event, event_data, event_data_stream, event_tag):
    """Writes the event to the output.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.
    """
    try:
      self.WriteEventBody(event, event_data, event_data_stream, event_tag)

    except errors.NoFormatterFound as exception:
      error_message = 'unable to retrieve formatter with error: {0!s}'.format(
          exception)
      self._ReportEventError(event, event_data, error_message)

    except errors.WrongFormatter as exception:
      error_message = 'wrong formatter with error: {0!s}'.format(exception)
      self._ReportEventError(event, event_data, error_message)

  @abc.abstractmethod
  def WriteEventBody(self, event, event_data, event_data_stream, event_tag):
    """Writes event values to the output.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.
    """

  def WriteEventMACBGroup(self, event_macb_group):
    """Writes an event MACB group to the output.

    An event MACB group is a group of events that have the same timestamp and
    event data (attributes and values), where the timestamp description (or
    usage) is one or more of MACB (modification, access, change, birth).

    This function is called if the psort engine detected an event MACB group
    so that the output module, if supported, can represent the group as
    such. If not overridden this function will output every event individually.

    Args:
      event_macb_group (list[tuple[EventObject, EventData, EventDataStream,
          EventTag]]): group of events with identical timestamps, attributes
          and values.
    """
    for event, event_data, event_data_stream, event_tag in event_macb_group:
      self.WriteEvent(event, event_data, event_data_stream, event_tag)

  def WriteFooter(self):
    """Writes the footer to the output.

    Can be used for post-processing or output after the last event
    is written, such as writing a file footer.
    """
    return

  def WriteHeader(self):
    """Writes the header to the output.

    Can be used for pre-processing or output before the first event
    is written, such as writing a file header.
    """
    return


class LinearOutputModule(OutputModule):
  """Linear output module."""

  def __init__(self, output_mediator, event_formatting_helper):
    """Initializes a linear output module.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfvfs.
      event_formatting_helper (EevntFormattingHelper): event formatting helper.
    """
    super(LinearOutputModule, self).__init__(output_mediator)
    self._event_formatting_helper = event_formatting_helper
    self._output_writer = None

  def WriteEventBody(self, event, event_data, event_data_stream, event_tag):
    """Writes event values to the output.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.
    """
    output_text = self._event_formatting_helper.GetFormattedEvent(
        event, event_data, event_data_stream, event_tag)

    output_text = '{0:s}\n'.format(output_text)
    self._output_writer.Write(output_text)

  def SetOutputWriter(self, output_writer):
    """Set the output writer.

    Args:
      output_writer (CLIOutputWriter): output writer.
    """
    self._output_writer = output_writer

  def Close(self):
    """Closes the output."""
    self._output_writer = None
