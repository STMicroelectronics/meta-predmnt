#!/usr/bin/env python3

################################################################################
# COPYRIGHT(c) 2022 STMicroelectronics                                         #
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
# This application helps configuring the Predictive Maintenance Platform on a
# gateway.


# IMPORT

from __future__ import print_function
import os
import signal
import json
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from utils import aws_utils
from utils import fs_utils
from utils import gtk_utils
from utils import definitions


# CONSTANTS

# Information.
INFORMATION = \
"""1) Log in to the dashboard
2) Configure your devices and copy the *.zip credentials to a USB key
3) Configure your edge gateway and copy the *.zip credentials to the USB key
4) Assign the devices to the edge gateway
5) Plug the USB key into the gateway and install the credentials here below
6) Deploy the solution from the dashboard to the gateway"""

# Setup.
MAXIMUM_NUMBER_OF_DEVICES = 4


# CLASSES

#
# Main window class.
#
class SetupPMPWindow(Gtk.Window):

    #
    # Constructor.
    #
    def __init__(self):
        super(SetupPMPWindow, self).__init__()
        self.set_title('PREDICTIVE MAINTENANCE PLATFORM SETUP')
        self.maximize()
        self.set_border_width(gtk_utils.DEFAULT_SPACE)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect('destroy', Gtk.Widget.destroy)
        self.main_grid = Gtk.Grid()
        self.main_grid.set_row_spacing(gtk_utils.DEFAULT_SPACE)
        self.main_grid.set_column_spacing(gtk_utils.DEFAULT_SPACE)
        self.main_grid.set_row_homogeneous(False)
        self.main_grid.set_column_homogeneous(True)
        self.main_grid.set_vexpand(True)
        self.main_grid.set_hexpand(True)
        self.add(self.main_grid)

        self.information_frame = Gtk.Frame()
        self.information_frame.set_label('Instructions')
        self.information_grid = Gtk.Grid()
        self.information_grid.set_row_spacing(gtk_utils.DEFAULT_SPACE)
        self.information_grid.set_column_spacing(gtk_utils.DEFAULT_SPACE)
        self.information_grid.set_column_homogeneous(True)
        self.information_grid.set_row_homogeneous(False)
        self.information_grid.set_border_width(gtk_utils.DEFAULT_SPACE)
        self.information_frame.add(self.information_grid)
        self.information_textbuffer = Gtk.TextBuffer()
        self.information_textview = Gtk.TextView.new_with_buffer(
            self.information_textbuffer)
        self.information_textview.connect('button-press-event',
            gtk_utils.textview_clicked)
        self.information_textview.set_border_width(gtk_utils.DEFAULT_SPACE)
        self.information_textview.set_editable(False)
        self.information_grid.add(self.information_textview)
        gtk_utils.write_to_buffer(
            self.information_textbuffer, INFORMATION)
        self.information_frame.set_hexpand(True)
        self.main_grid.attach(self.information_frame, 0, 0, 2, 1)

        self.edge_gateway_frame = Gtk.Frame()
        self.edge_gateway_frame.set_label('Edge Gateway Credentials')
        self.edge_gateway_frame.set_vexpand(True)
        self.edge_gateway_grid = Gtk.Grid()
        self.edge_gateway_grid.set_border_width(gtk_utils.DEFAULT_SPACE)
        self.edge_gateway_grid.set_column_spacing(gtk_utils.DEFAULT_SPACE)
        self.edge_gateway_frame.add(self.edge_gateway_grid)
        self.edge_gateway = None
        self.edge_gateway_textbuffer = Gtk.TextBuffer()
        self.edge_gateway_textview = Gtk.TextView.new_with_buffer(
            self.edge_gateway_textbuffer)
        self.edge_gateway_textview.connect('button-press-event',
            gtk_utils.textview_clicked)
        self.edge_gateway_textview.set_border_width(gtk_utils.DEFAULT_SPACE)
        self.edge_gateway_textview.set_editable(False)
        self.edge_gateway_textview_scrolling = Gtk.ScrolledWindow()
        self.edge_gateway_textview_scrolling.add(self.edge_gateway_textview)
        self.edge_gateway_textview_scrolling.set_vexpand(True)
        self.edge_gateway_textview_scrolling.set_hexpand(True)
        self.edge_gateway_add_button = Gtk.Button.new_with_label('Add')
        self.edge_gateway_add_button.connect('clicked',
            self.on_add_edge_gateway_clicked)
        self.edge_gateway_grid.attach(self.edge_gateway_add_button, 0, 0, 1, 1)
        self.edge_gateway_grid.attach(self.edge_gateway_textview_scrolling, 1, 0, 1, 1)
        self.main_grid.attach(self.edge_gateway_frame, 0, 1, 1, 1)

        self.devices_frame = Gtk.Frame()
        self.devices_frame.set_label('Devices Credentials')
        self.devices_frame.set_vexpand(True)
        self.devices_grid = Gtk.Grid()
        self.devices_grid.set_border_width(gtk_utils.DEFAULT_SPACE)
        self.devices_grid.set_column_spacing(gtk_utils.DEFAULT_SPACE)
        self.devices_frame.add(self.devices_grid)
        self.devices_dict = {}
        self.devices_textbuffer = Gtk.TextBuffer()
        self.devices_textview = Gtk.TextView.new_with_buffer(
            self.devices_textbuffer)
        self.devices_textview.connect('button-press-event',
            gtk_utils.textview_clicked)
        self.devices_textview.set_border_width(gtk_utils.DEFAULT_SPACE)
        self.devices_textview.set_editable(False)
        self.devices_textview_scrolling = Gtk.ScrolledWindow()
        self.devices_textview_scrolling.add(self.devices_textview)
        self.devices_textview_scrolling.set_vexpand(True)
        self.devices_textview_scrolling.set_hexpand(True)
        self.device_add_button = Gtk.Button.new_with_label('Add')
        self.device_add_button.connect('clicked',
            self.on_add_devices_clicked)
        self.devices_grid.attach(self.device_add_button, 0, 0, 1, 1)
        self.devices_grid.attach(self.devices_textview_scrolling, 1, 0, 1, 1)
        self.main_grid.attach(self.devices_frame, 1, 1, 1, 1)

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
        self.console_grid.attach(self.console_textview_scrolling, 0, 0, 2, 1)
        self.console_textview.connect('size-allocate',
            gtk_utils.on_textview_change,
            self.console_textview_scrolling)
        self.main_grid.attach(self.console_frame, 0, 2, 2, 1)

        self.configure_button = Gtk.Button.new_with_label('Install Credentials')
        self.configure_button.connect('clicked', self.on_configure_clicked)

        self.show_button = Gtk.Button.new_with_label('Show Configuration')
        self.show_button.connect('clicked', self.on_show_clicked)

        self.close_button = Gtk.Button.new_with_label('Close')
        self.close_button.connect('clicked', self.on_close_clicked)

        self.hbox = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=gtk_utils.DEFAULT_SPACE)
        self.hbox.set_homogeneous(True)
        self.hbox.set_hexpand(True)
        self.hbox.add(self.configure_button)
        self.hbox.add(self.show_button)
        self.hbox.add(self.close_button)
        self.main_grid.attach(self.hbox, 0, 3, 2, 1)

        # self.edge_gateway = '/media/usb/AG_Edge.zip'
        # self.devices_dict['Position 1'] = '/media/usb/AG_Device_1.zip'
        # self.devices_dict['Position 4'] = '/media/usb/AG_Device_2.zip'

        self.set_buttons_status()


    #
    # Check install arguments.
    #
    def set_buttons_status(self):
        self.edge_gateway_add_button.set_sensitive(True)
        self.device_add_button.set_sensitive(True)
        self.show_button.set_sensitive(os.path.exists(
            definitions.PMP_CONFIGURATION_PATH))
        status = True if self.edge_gateway and self.devices_dict else False
        self.configure_button.set_sensitive(status)

    #
    # Callback for "Add" button clicked for edge gateway.
    #
    def on_add_edge_gateway_clicked(self, widget):
        fs_utils.mount_usb_key()
        dialog = Gtk.FileChooserDialog(
            title='Select Edge Credentials zip file',
            parent=self,
            action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK)
        #dialog.maximize()
        self.screen_width = self.get_screen().get_width()
        self.screen_height = self.get_screen().get_height()
        self.set_default_size(self.screen_width, self.screen_height)
        credentials_filter = Gtk.FileFilter()
        credentials_filter.set_name("Credential Zip files")
        credentials_filter.add_pattern("*.zip")
        dialog.add_filter(credentials_filter)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.edge_gateway = dialog.get_filename()
            gtk_utils.delete_buffer(self.edge_gateway_textbuffer)
            gtk_utils.write_to_buffer(self.edge_gateway_textbuffer, '%s\n' % \
                (os.path.basename(self.edge_gateway)))
        self.set_buttons_status()
        dialog.destroy()

    #
    # Callback for "Add" button clicked for devices.
    #
    def on_add_devices_clicked(self, widget):
        fs_utils.mount_usb_key()
        dialog = Gtk.FileChooserDialog(
            title='Select Device Credentials zip file',
            parent=self,
            action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK)
        #dialog.maximize()
        self.screen_width = self.get_screen().get_width()
        self.screen_height = self.get_screen().get_height()
        self.set_default_size(self.screen_width, self.screen_height)
        credentials_filter = Gtk.FileFilter()
        credentials_filter.set_name("Credential Zip files")
        credentials_filter.add_pattern("*.zip")
        dialog.add_filter(credentials_filter)
        position_box = gtk_utils.StringComboBox(
            'Position', 1, MAXIMUM_NUMBER_OF_DEVICES)
        dialog.set_extra_widget(position_box.get_widget())
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            position = position_box.get_widget().get_active_text()
            for key in [key for key, value in self.devices_dict.items() if filename == value]:
                del self.devices_dict[key]
            self.devices_dict[position] = filename
            gtk_utils.delete_buffer(self.devices_textbuffer)
            for key, value in sorted(self.devices_dict.items()):
                gtk_utils.write_to_buffer(self.devices_textbuffer, '%s: %s\n' % \
                    (key, os.path.basename(value)))
        self.set_buttons_status()
        dialog.destroy()

    #
    # Callback for "Configure" button clicked.
    #
    def on_configure_clicked(self, widget):
        self.configure_button.set_sensitive(False)
        self.edge_gateway_add_button.set_sensitive(False)
        self.device_add_button.set_sensitive(False)
        self.show_button.set_sensitive(False)
        self.on_configure_thread = \
            gtk_utils.ProgressBarWindowThread(self.on_configure)
        self.on_configure_thread.start()

    #
    # Configure callback.
    #
    def on_configure(self, progress_bar_window):
        fs_utils.mount_usb_key()
        progress_bar_window.set_text('Installing credentials...')
        gtk_utils.write_to_buffer(self.console_textbuffer,
            'Installing credentials...\n')
        fs_utils.create_file_from_json(
            definitions.PMP_CONFIGURATION_PATH,
            definitions.DEFAULT_PMP_CONFIGURATION_JSON)
        aws_utils.configure_edge_gateway_aws(
            self.edge_gateway, self.console_textbuffer)
        aws_utils.configure_devices_aws(
            self.devices_dict, self.console_textbuffer)
        fs_utils.unmount_usb_key()
        progress_bar_window.set_text('Restarting AWS Greengrass...')
        gtk_utils.write_to_buffer(self.console_textbuffer,
            'Credentials installed.\nRestarting AWS Greengrass...')
        aws_utils.restart_aws_greengrass()
        progress_bar_window.set_text('Waiting for deployment...')
        gtk_utils.write_to_buffer(self.console_textbuffer,
            'Done.\nWaiting for deployment...')
        aws_utils.wait_for_aws_deployment()
        gtk_utils.write_to_buffer(self.console_textbuffer, 'Done.\n')
        self.edge_gateway = None
        self.devices_dict = {}
        gtk_utils.delete_buffer(self.edge_gateway_textbuffer)
        gtk_utils.delete_buffer(self.devices_textbuffer)
        self.set_buttons_status()

    #
    # Callback for "Show" button clicked.
    #
    def on_show_clicked(self, widget):
        with open(definitions.PMP_CONFIGURATION_PATH, 'r') as fp:
            configuration_json = json.load(fp)
        window = gtk_utils.MessageWindow(
            "JSON CONFIGURATION FILE",
            "Configuration",
            json.dumps(configuration_json, indent=4, sort_keys=True),
            True)
        window.show_all()

    #
    # Callback for "Close" button clicked.
    #
    def on_close_clicked(self, widget):
        self.destroy()


# RUNNING MAIN APPLICATION

if __name__ == "__main__":
    # Adding signal to catch 'CRTL+C'.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    try:
        main_window = SetupPMPWindow()
        main_window.show_all()
        Gtk.main()
    except Exception as e:
        print(e)

