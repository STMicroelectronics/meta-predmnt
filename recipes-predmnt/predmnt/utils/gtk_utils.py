#!/usr/bin/env python

################################################################################
# COPYRIGHT(c) 2018 STMicroelectronics                                         #
#                                                                              #
# Redistribution and use in source and binary forms, with or without           #
# modification, are permitted provided that the following conditions are met:  #
#   1. Redistributions of source code must retain the above copyright notice,  #
#      this list of conditions and the following disclaimer.                   #
#   2. Redistributions in binary form must reproduce the above copyright       #
#      notice, this list of conditions and the following disclaimer in the     #
#      documentation and/or other materials provided with the distribution.    #
#   3. Neither the name of STMicroelectronics nor the names of its             #
#      contributors may be used to endorse or promote products derived from    #
#      this software without specific prior written permission.                #
#                                                                              #
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"  #
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE    #
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE   #
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE    #
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR          #
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF         #
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS     #
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN      #
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)      #
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE   #
# POSSIBILITY OF SUCH DAMAGE.                                                  #
################################################################################

################################################################################
# Author:  Davide Aliprandi, STMicroelectronics                                #
################################################################################


# DESCRIPTION
#
# This file provides useful functions.


# IMPORT

from __future__ import print_function
import os
import subprocess
import threading
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GLib


# CONSTANTS

# GTK.
DEFAULT_SPACE = 8
PROGRESS_BAR_TIMEOUT_ms = 50


# FUNCTIONS

#
# Clear a buffer.
#
def delete_buffer(buffer):
    buffer.delete(buffer.get_start_iter(), buffer.get_end_iter())
    while Gtk.events_pending():
        Gtk.main_iteration()

#
# Write a message to a buffer.
# Blocking call.
#
def write_to_buffer(buffer, message):
    buffer.insert(buffer.get_end_iter(), message)
    while Gtk.events_pending():
        Gtk.main_iteration()

#
# Execute a command and write its output to a buffer.
# Non-blocking call by default.
# When run in blocking mode it may miss some text to write to the given buffer.
#
def execute_command_and_write_to_buffer(command, buffer, blocking=False):
    process = subprocess.Popen(
        command, shell = True, stdout = subprocess.PIPE)
    GLib.io_add_watch(
        process.stdout,
        GLib.IO_IN,
        write_to_buffer_callback,
        buffer)
    if blocking:
        process.wait()

#
# Callback for writing to buffer.
#
def write_to_buffer_callback(fd, condition, buffer):
    if condition == GLib.IO_IN:
        line = fd.readline().decode("utf-8")
        buffer.insert_at_cursor(line)
        while Gtk.events_pending():
            Gtk.main_iteration()
        return True
    return False

#
# Callback for textview changes (e.g. scrolling).
#
def on_textview_change(a, b, textview_scrolling):
    adj = textview_scrolling.get_vadjustment()
    adj.set_value(adj.get_upper())

#
# Callback for ignoring clicks within a textview.
#
def textview_clicked(widget, event):
    return True


# CLASSES

#
# Class to visualize a progress bar.
#
class ProgressBarWindow(Gtk.Window):

    #
    # Constructor.
    #
    def __init__(self, text=''):
        Gtk.Window.__init__(self)
        self.screen_width = self.get_screen().get_width()
        self.screen_height = self.get_screen().get_height()
        self.set_default_size(self.screen_height / 2, 0)
        self.set_border_width(DEFAULT_SPACE)
        self.set_position(Gtk.WindowPosition.CENTER)

        hbox = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=DEFAULT_SPACE)
        self.add(hbox)

        self.progressbar = Gtk.ProgressBar()
        hbox.pack_start(self.progressbar, True, True, 0)

        self.progress_callback_id = GLib.timeout_add(
            PROGRESS_BAR_TIMEOUT_ms,
            self.on_timeout,
            None)

        self.set_text(text)
        self.show_all()

    #
    # Set the text of the progress bar.
    #
    def set_text(self, text):
        self.set_title(text)
        #self.progressbar.set_text(text)
        #self.progressbar.set_show_text(True)

    #
    # Callback for progress bar's update.
    #
    def on_timeout(self, user_data):
        self.progressbar.pulse()
        return True


#
# Class to open a progress bar window.
#
class ProgressBarWindowThread(threading.Thread):

    #
    # Constructor.
    #
    def __init__(self, run_callback):
        threading.Thread.__init__(self)
        self._run_callback = run_callback
        self._pbw = ProgressBarWindow()

    #
    # Start the thread.
    #
    def run(self):
        self._run_callback(self._pbw)
        self._pbw.destroy()


#
# String ComboBox class.
#
class StringComboBox(Gtk.Box):

    #
    # Constructor.
    #
    def __init__(self, name, minimum, maximum):
        Gtk.Box.__init__(self)
        self.combo = Gtk.ComboBoxText()
        self.combo.set_entry_text_column(0)
        for position in range(minimum, maximum + 1):
            self.combo.append_text('%s %s' % (name, str(position)))
        #self.combo.connect("changed", self.on_combo_changed)
        self.combo.set_active(maximum - 1)

    #
    # Get the widget.
    #
    def get_widget(self):
        return self.combo

    #
    # Callback for "changed" event.
    #
    def on_combo_changed(self, combo):
        #print(combo.get_active_text())
        pass


#
# Class to show a message in a window.
#
class MessageWindow(Gtk.Window):

    #
    # Constructor.
    #
    def __init__(self, title, message):
        super(MessageWindow, self).__init__()
        self.set_title(title)
        self.maximize()
        self.set_border_width(DEFAULT_SPACE)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect('destroy', Gtk.Widget.destroy)
        self.main_grid = Gtk.Grid()
        self.main_grid.set_row_spacing(DEFAULT_SPACE)
        self.main_grid.set_column_spacing(DEFAULT_SPACE)
        self.main_grid.set_row_homogeneous(False)
        self.main_grid.set_column_homogeneous(True)
        self.main_grid.set_vexpand(True)
        self.main_grid.set_hexpand(True)
        self.add(self.main_grid)

        self.message_frame = Gtk.Frame()
        self.message_frame.set_label('Console')
        self.message_grid = Gtk.Grid()
        self.message_grid.set_row_spacing(DEFAULT_SPACE)
        self.message_grid.set_column_spacing(DEFAULT_SPACE)
        self.message_grid.set_column_homogeneous(True)
        self.message_grid.set_row_homogeneous(False)
        self.message_grid.set_border_width(DEFAULT_SPACE)
        self.message_frame.add(self.message_grid)
        self.message_textbuffer = Gtk.TextBuffer()
        self.message_textview = Gtk.TextView.new_with_buffer(
            self.message_textbuffer)
        self.message_textview.connect('button-press-event',
            textview_clicked)
        self.message_textview.set_editable(False)
        self.message_textview_scrolling = Gtk.ScrolledWindow()
        self.message_textview_scrolling.add(self.message_textview)
        self.message_textview_scrolling.set_vexpand(True)
        self.message_grid.attach(self.message_textview_scrolling, 0, 0, 2, 1)
        self.message_textview.connect('size-allocate',
            on_textview_change,
            self.message_textview_scrolling)
        self.main_grid.attach(self.message_frame, 0, 0, 1, 1)

        self.close_button = Gtk.Button('Close')
        self.close_button.connect('clicked', self.on_close_clicked)
        self.main_grid.attach(self.close_button, 0, 1, 1, 1)

        write_to_buffer(self.message_textbuffer, message)

        self.show_all()

    #
    # Callback for "Close" button clicked.
    #
    def on_close_clicked(self, widget):
        self.destroy()
