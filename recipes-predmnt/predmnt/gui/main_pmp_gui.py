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
# This application is the entry application to setup and run the Predictive
# Maintenance Platform on a gateway.


# IMPORT

from __future__ import print_function
import signal
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from utils import gtk_utils
from utils import definitions


# CLASSES

#
# Main window class.
#
class MainPMPWindow(Gtk.Window):

    #
    # Constructor.
    #
    def __init__(self):
        super(MainPMPWindow, self).__init__()
        self.set_title('PREDICTIVE MAINTENANCE PLATFORM')
        self.maximize()
        # self.screen_width = self.get_screen().get_width()
        # self.screen_height = self.get_screen().get_height()
        # self.set_default_size(self.screen_width, self.screen_height)
        self.set_border_width(gtk_utils.DEFAULT_SPACE)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect('destroy', Gtk.main_quit)

        self.vbox = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=gtk_utils.DEFAULT_SPACE)
        self.vbox.set_homogeneous(False)
        self.vbox.set_vexpand(True)
        self.vbox.set_hexpand(True)
        self.add(self.vbox)
        # self.hbox_top = Gtk.Box(
        #     orientation=Gtk.Orientation.HORIZONTAL, spacing=gtk_utils.DEFAULT_SPACE)
        self.hbox_center = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=gtk_utils.DEFAULT_SPACE)
        self.hbox_center.set_homogeneous(True)
        self.hbox_center.set_vexpand(True)
        self.hbox_center.set_hexpand(True)
        # self.hbox_bottom = Gtk.Box(
        #     orientation=Gtk.Orientation.HORIZONTAL, spacing=gtk_utils.DEFAULT_SPACE)
        # self.vbox.add(self.hbox_top)
        self.vbox.add(self.hbox_center)
        # self.vbox.add(self.hbox_bottom)

        self.setup_gw_button = Gtk.Button()#'  (1)\n SETUP\nGATEWAY')
        self.setup_gw_button.props.relief = Gtk.ReliefStyle.NONE
        self.setup_gw_button.connect("enter-notify-event", self.on_leave)
        self.setup_gw_button.connect('clicked',
            self.on_setup_gw_clicked)
        image = Gtk.Image()
        image.set_from_file(
            definitions.PMP_PATH + '/media/setup_gateway_blue.png')
        self.setup_gw_button.add(image)
        self.setup_gw_button.set_size_request(230, 230)

        self.setup_pmp_button = Gtk.Button()#'    (2)\n   SETUP\nAPPLICATION')
        self.setup_pmp_button.props.relief = Gtk.ReliefStyle.NONE
        self.setup_pmp_button.connect("enter-notify-event", self.on_leave)
        self.setup_pmp_button.connect('clicked',
            self.on_setup_pmp_clicked)
        image = Gtk.Image()
        image.set_from_file(
            definitions.PMP_PATH + '/media/setup_application_lightblue.png')
        self.setup_pmp_button.add(image)
        self.setup_pmp_button.set_size_request(230, 230)

        self.start_pmp_button = Gtk.Button()#'    (3)\n    RUN\nAPPLICATION')
        self.start_pmp_button.props.relief = Gtk.ReliefStyle.NONE
        self.start_pmp_button.connect("enter-notify-event", self.on_leave)
        self.start_pmp_button.connect('clicked',
            self.on_pmp_clicked)
        image = Gtk.Image()
        image.set_from_file(
            definitions.PMP_PATH + '/media/run_application_magenta.png')
        self.start_pmp_button.add(image)
        self.start_pmp_button.set_size_request(230, 230)

        #self.close_button = Gtk.Button.new_with_label('Close')
        #self.close_button.connect('clicked', self.on_close_clicked)

        self.hbox_center.add(self.setup_gw_button)
        self.hbox_center.add(self.setup_pmp_button)
        self.hbox_center.add(self.start_pmp_button)

        #self.vbox.add(self.close_button)

    #
    # Callback for "Setup Gateway" button clicked.
    #
    def on_setup_gw_clicked(self, widget):
        import setup_gw_gui
        gui = setup_gw_gui.SetupGwWindow()
        gui.show_all()

    #
    # Callback for "Setup Application" button clicked.
    #
    def on_setup_pmp_clicked(self, widget):
        import setup_pmp_gui
        gui = setup_pmp_gui.SetupPMPWindow()
        gui.show_all()

    #
    # Callback for "Start Application" button clicked.
    #
    def on_pmp_clicked(self, widget):
        import run_pmp_gui
        gui = run_pmp_gui.RunPMPWindow()
        gui.show_all()

    #
    # Callback for "Close" button clicked.
    #
    def on_close_clicked(self, widget):
        self.destroy()

    #
    # Callback for "enter-notify-event" event.
    #
    def on_leave(self, btn, event):
        return True


# RUNNING MAIN APPLICATION

if __name__ == "__main__":
    # Adding signal to catch 'CRTL+C'.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    try:
        main_window = MainPMPWindow()
        main_window.show_all()
        Gtk.main()
    except Exception as e:
        print(e)

