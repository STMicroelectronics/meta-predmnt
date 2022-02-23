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
# This application installs all the required components to run the Predictive
# Maintenance Platform on a gateway.


# IMPORT

from __future__ import print_function
import os
import subprocess
import signal
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
#from gi.repository import GLib

from utils import aws_utils
from utils import fs_utils
from utils import gtk_utils
from utils import definitions


# CONSTANTS

# GTK.
TIMEOUT_ms = 1000


# CLASSES

#
# Main window class.
#
class SetupGwWindow(Gtk.Window):

    #
    # Constructor.
    #
    def __init__(self):
        super(SetupGwWindow, self).__init__()
        self.set_title('GATEWAY SETUP FOR PREDICTIVE MAINTENANCE PLATFORM')
        self.maximize()
        self.set_border_width(gtk_utils.DEFAULT_SPACE)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect('destroy', Gtk.Widget.destroy)
        self.main_grid = Gtk.Grid()
        self.main_grid.set_row_spacing(gtk_utils.DEFAULT_SPACE)
        self.main_grid.set_row_homogeneous(False)
        self.main_grid.set_vexpand(True)
        self.main_grid.set_hexpand(True)
        self.add(self.main_grid)

        self.connection_frame = Gtk.Frame()
        self.connection_frame.set_label('Connection')
        self.connection_grid = Gtk.Grid()
        self.connection_grid.set_row_spacing(gtk_utils.DEFAULT_SPACE)
        self.connection_grid.set_column_spacing(gtk_utils.DEFAULT_SPACE)
        self.connection_grid.set_column_homogeneous(True)
        self.connection_grid.set_border_width(gtk_utils.DEFAULT_SPACE)
        self.connection_frame.add(self.connection_grid)
        self.ethernet_button = Gtk.RadioButton()
        self.ethernet_button.set_label('Ethernet')
        self.wifi_button = Gtk.RadioButton.new_from_widget(
            self.ethernet_button)
        self.wifi_button.set_label('WiFi')
        self.wifi_button.connect('toggled', self.on_wifi_button_toggled)
        self.wifi_button.set_active(False)
        self.connection_grid.attach(self.ethernet_button, 0, 0, 1, 1)
        self.connection_grid.attach(self.wifi_button, 0, 1, 1, 1)
        self.connection_ssid_label = Gtk.Label('SSID')
        self.connection_ssid_label_box = Gtk.Box()
        self.connection_ssid_label_box.props.halign = Gtk.Align.END
        self.connection_ssid_label_box.add(self.connection_ssid_label)
        self.connection_grid.attach(self.connection_ssid_label_box, 1, 0, 1, 1)
        self.connection_ssid_entry = Gtk.Entry()
        self.connection_grid.attach(self.connection_ssid_entry, 2, 0, 1, 1)
        self.connection_password_label = Gtk.Label('Password')
        self.connection_password_label_box = Gtk.Box()
        self.connection_password_label_box.props.halign = Gtk.Align.END
        self.connection_password_label_box.add(self.connection_password_label)
        self.connection_grid.attach(self.connection_password_label_box, 1, 1, 1, 1)
        self.connection_password_entry = Gtk.Entry()
        self.connection_password_entry.set_visibility(False)
        self.connection_password_entry.set_invisible_char('*')
        self.connection_grid.attach(self.connection_password_entry, 2, 1, 1, 1)
        self.connect_button = Gtk.Button.new_with_label('Connect')
        self.connect_button.connect('clicked', self.on_connect_clicked)
        self.connection_grid.attach(self.connect_button, 0, 2, 3, 1)
        self.main_grid.attach(self.connection_frame, 0, 0, 1, 1)

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
        self.console_grid.attach(self.console_textview_scrolling, 0, 0, 3, 1)
        self.console_textview.connect('size-allocate',
            gtk_utils.on_textview_change,
            self.console_textview_scrolling)
        self.main_grid.attach(self.console_frame, 0, 1, 1, 1)

        self.update_button = Gtk.Button.new_with_label('Update')
        self.update_button.connect('clicked', self.on_update_clicked)

        self.close_button = Gtk.Button.new_with_label('Close')
        self.close_button.connect('clicked', self.on_close_clicked)

        self.hbox = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=gtk_utils.DEFAULT_SPACE)
        self.hbox.set_homogeneous(True)
        self.hbox.set_hexpand(True)
        self.hbox.add(self.update_button)
        self.hbox.add(self.close_button)
        self.main_grid.attach(self.hbox, 0, 2, 3, 1)

        self.wifi_button.emit('toggled')

    #
    # Callback for "WiFi" button toggled. 
    #
    def on_wifi_button_toggled(self, widget):
        active = widget.get_active()
        self.connection_ssid_label.set_sensitive(active)
        self.connection_ssid_entry.set_sensitive(active)
        self.connection_password_label.set_sensitive(active)
        self.connection_password_entry.set_sensitive(active)
        self.connect_button.set_sensitive(active)
        self.connect_button_status = active
        self.check_wifi()

    #
    # Callback for "Connect" button clicked.
    #
    def on_connect_clicked(self, widget):
        self.connect_button.set_sensitive(False)
        self.update_button.set_sensitive(False)
        self.on_connect_thread = gtk_utils.ProgressBarWindowThread(self.on_connect)
        self.on_connect_thread.start()

    #
    # Connect callback.
    #
    def on_connect(self, progress_bar_window):
        gtk_utils.delete_buffer(self.console_textbuffer)
        connection_ssid = self.connection_ssid_entry.get_text()
        connection_password = self.connection_password_entry.get_text()
        if not (connection_ssid and connection_password):
            self.connect_button.set_sensitive(True)
            self.update_button.set_sensitive(True)
            gtk_utils.write_to_buffer(
                self.console_textbuffer, 'Insert valid SSID and password.\n')
            return
        progress_bar_window.set_text('Connecting...')
        gtk_utils.write_to_buffer(
            self.console_textbuffer, 'Connecting to %s...' % (connection_ssid))
        fs_utils.create_wifi_scripts(connection_ssid, connection_password)
        ip_address = None
        try:
            os.system(fs_utils.DISCONNECT_WIFI_PATH)
            os.system(fs_utils.CONNECT_WIFI_PATH)
            output = subprocess.check_output('ifconfig | grep \'wlan\' -A1 | grep inet',
                stderr=subprocess.STDOUT, shell=True).decode('utf-8')
            ip_address = output.split()[1].split(':')[1]
        except subprocess.CalledProcessError as e:
            pass
        if ip_address:
            gtk_utils.write_to_buffer(
                self.console_textbuffer, 
                'Connected with ip address %s.\n' \
                'From Bash use \"%s\" or \"%s\".\n' \
                % (ip_address, fs_utils.CONNECT_WIFI_PATH, fs_utils.DISCONNECT_WIFI_PATH))
        else:
            gtk_utils.write_to_buffer(
                self.console_textbuffer, 
                'Impossible to connect to %s' % (connection_ssid))
        self.connect_button.set_sensitive(True)
        self.update_button.set_sensitive(True)

    #
    # Callback for "Configure" button clicked.
    #
    def on_update_clicked(self, widget):
        self.connect_button_status = self.connect_button.get_sensitive()
        self.connect_button.set_sensitive(False)
        self.update_button.set_sensitive(False)
        self.on_connect_thread = gtk_utils.ProgressBarWindowThread(self.on_configure)
        self.on_connect_thread.start()

    #
    # Callback for "Configure" button clicked.
    #
    def on_configure(self, progress_bar_window):
        # Adding user and group to the system.
        progress_bar_window.set_text('Configuring...')
        gtk_utils.write_to_buffer(
            self.console_textbuffer, 'Adding user and group to the system...\n')
        try:
            command = 'adduser --system ggc_user 2>&1'
            output = subprocess.check_output(command,
                stderr=subprocess.STDOUT, shell=True).decode('utf-8')
            gtk_utils.write_to_buffer(self.console_textbuffer, output)
        except subprocess.CalledProcessError as e:
            pass
        try:
            command = 'addgroup --system ggc_group 2>&1'
            output = subprocess.check_output(command,
                stderr=subprocess.STDOUT, shell=True).decode('utf-8')
            gtk_utils.write_to_buffer(self.console_textbuffer, output)
        except subprocess.CalledProcessError as e:
            pass

        # Enabling hardlink and softlink protection at operating system start-up.
        gtk_utils.write_to_buffer(
            self.console_textbuffer,
            'Enabling hardlink and softlink protection at operating system ' \
            'start-up...\n')
        fd = open(definitions.GATEWAY_RULES_PATH, 'w')
        fd.write('fs.protected_hardlinks = 1\nfs.protected_symlinks = 1')
        fd.close()

        # Installing Python packages.
        gtk_utils.write_to_buffer(
            self.console_textbuffer, 'Installing Python packages...\n')
        command = '%s 2>&1' % (definitions.PYTHON_PIP_UPGRADE)
        gtk_utils.execute_command_and_write_to_buffer(
            command, self.console_textbuffer)
        if self.check_setup(None):
            command = 'pip3 install %s 2>&1' % (definitions.PYTHON_PACKAGES_TO_INSTALL)
            gtk_utils.execute_command_and_write_to_buffer(
                command, self.console_textbuffer)
            #GLib.timeout_add(TIMEOUT_ms, self.check_setup, None)
            while self.check_setup(None):
                pass
        else:
            gtk_utils.write_to_buffer(
                self.console_textbuffer,
                'Python packages installed.\n')
        self.connect_button.set_sensitive(self.connect_button_status)
        self.update_button.set_sensitive(True)

    #
    # Callback for "Close" button clicked.
    #
    def on_close_clicked(self, widget):
        self.destroy()

    #
    # Checking whether the setup has been completed.
    #
    def check_setup(self, user_data):
        import imp
        import pkg_resources
        #from pip._internal.utils.misc import get_installed_distributions
        imp.reload(pkg_resources)
        installed_packages = set(package.key for package in pkg_resources.working_set) 
        #installed_packages = get_installed_distributions(local_only=False)
        #installed_packages = set(package.project_name for package in installed_packages)
        if set(definitions.PYTHON_PACKAGES_TO_INSTALL.split(' ')).issubset(installed_packages):
            return False
        return True

    #
    # Check whether a WiFi network has been configured.
    #
    def check_wifi(self):
        if os.path.exists(fs_utils.CONFIGURATION_WIFI_PATH):
            try:
                connection_ssid = subprocess.check_output('cat %s | grep ssid' \
                    % (fs_utils.CONFIGURATION_WIFI_PATH), \
                    stderr=subprocess.STDOUT, shell=True).decode('utf-8').split('\"')[1]
                connection_password = subprocess.check_output('cat %s | grep \#psk' \
                    % (fs_utils.CONFIGURATION_WIFI_PATH), \
                    stderr=subprocess.STDOUT, shell=True).decode('utf-8').split('\"')[1]
                if connection_ssid != None and connection_password != None:
                    self.connection_ssid_entry.set_text(connection_ssid)
                    self.connection_password_entry.set_text(connection_password)
                    return True
            except subprocess.CalledProcessError as e:
                pass
        return False


# RUNNING MAIN APPLICATION

if __name__ == "__main__":
    # Adding signal to catch 'CRTL+C'.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    try:
        main_window = SetupGwWindow()
        main_window.show_all()
        Gtk.main()
    except Exception as e:
        print(e)
