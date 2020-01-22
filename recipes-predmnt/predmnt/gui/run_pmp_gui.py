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
# This application implements a Predictive Maintenance application running on a
# gateway which collects data from IO-Link sensors and sends them to the Amazon
# AWS IoT cloud.


# IMPORT

from __future__ import print_function
import signal
import re
import subprocess
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GLib

from utils import aws_utils
from utils import gtk_utils
import pmp_definitions


# CONSTANTS

# URIs.
PMP_COMMAND = 'python3 -u %s/pmp.py -c %s' % \
    (pmp_definitions.PMP_PATH, pmp_definitions.PMP_CONFIGURATION_PATH)

# ALARMS.
ALARM_WINDOWS_TIMEOUT_ms = 5000 


# CLASSES

#
# Main window class.
#
class RunPMPWindow(Gtk.Window):

    #
    # Constructor.
    #
    def __init__(self):
        super(RunPMPWindow, self).__init__()
        self.set_title('PREDICTIVE MAINTENANCE PLATFORM RUNNING...')
        self.maximize()
        self.set_border_width(gtk_utils.DEFAULT_SPACE)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect('destroy', self.on_close_clicked)
        self.main_grid = Gtk.Grid()
        self.main_grid.set_row_spacing(gtk_utils.DEFAULT_SPACE)
        self.main_grid.set_row_homogeneous(False)
        self.main_grid.set_vexpand(True)
        self.main_grid.set_hexpand(True)
        self.add(self.main_grid)

        self.console_frame = Gtk.Frame()
        self.console_frame.set_label('Console')
        self.console_frame.set_vexpand(True)
        self.console_frame.set_hexpand(True)
        self.console_grid = Gtk.Grid()
        self.console_grid.set_row_spacing(gtk_utils.DEFAULT_SPACE)
        self.console_grid.set_column_spacing(gtk_utils.DEFAULT_SPACE)
        self.console_grid.set_column_homogeneous(True)
        self.console_grid.set_row_homogeneous(False)
        self.console_grid.set_border_width(gtk_utils.DEFAULT_SPACE)
        self.console_frame.add(self.console_grid)
        self.console_textbuffer = Gtk.TextBuffer()
        self.console_textview = Gtk.TextView.new_with_buffer(
            self.console_textbuffer)
        self.console_textview.connect('button-press-event',
            gtk_utils.textview_clicked)
        self.console_textview.set_editable(False)
        self.console_textview_scrolling = Gtk.ScrolledWindow()
        self.console_textview_scrolling.add(self.console_textview)
        self.console_textview_scrolling.set_vexpand(True)
        self.console_grid.attach(self.console_textview_scrolling, 0, 0, 1, 1)
        self.console_textview.connect('size-allocate',
            gtk_utils.on_textview_change,
            self.console_textview_scrolling)
        self.main_grid.attach(self.console_frame, 0, 1, 1, 1)

        self.stop_button = Gtk.Button('Close')
        self.stop_button.connect('clicked', self.on_close_clicked)
        self.main_grid.attach(self.stop_button, 0, 2, 1, 1)

        self.run_thread = gtk_utils.ProgressBarWindowThread(self.on_run)
        self.run_thread.start()

        self.pmp_process = None

    #
    # Prepare callback.
    #
    def on_run(self, progress_bar_window):
        progress_bar_window.set_text('Restarting AWS Greengrass...')
        gtk_utils.write_to_buffer(self.console_textbuffer, 'Restarting AWS Greengrass...')
        #aws_utils.restart_aws_greengrass()
        gtk_utils.write_to_buffer(self.console_textbuffer, 'Done.\nRunning the application...\n')
        self.pmp_process = self.execute_command_and_write_to_buffer(
            PMP_COMMAND, self.console_textbuffer)

    #
    # Callback for "Close" button clicked.
    #
    def on_close_clicked(self, widget):
        self.pmp_process.kill()
        self.destroy()

    #
    # Callback for "enter-notify-event" event.
    #
    def on_leave(self, btn, event):
        return True

    #
    # Execute a command and write its output to a buffer.
    # Non-blocking call by default.
    # When run in blocking mode it may miss some text to write to the given buffer.
    #
    def execute_command_and_write_to_buffer(self, command, buffer, blocking=False):
        process = subprocess.Popen(
            command, shell = True, stdout = subprocess.PIPE)
        GLib.io_add_watch(
            process.stdout,
            GLib.IO_IN,
            self.write_to_buffer_callback,
            buffer)
        if blocking:
            process.wait()
        return process

    #
    # Callback for writing to buffer.
    #
    def write_to_buffer_callback(self, fd, condition, buffer):
        if condition == GLib.IO_IN:
            line = fd.readline().decode("utf-8")
            buffer.insert_at_cursor(line)
            while Gtk.events_pending():
                Gtk.main_iteration()
            return True
        return False


# RUNNING MAIN APPLICATION

if __name__ == "__main__":
    # Adding signal to catch 'CRTL+C'.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    try:
        main_window = RunPMPWindow()
        main_window.show_all()
        Gtk.main()
    except Exception as e:
        print(e)
