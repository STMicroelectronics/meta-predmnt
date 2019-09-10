#!/usr/bin/env python

################################################################################
# COPYRIGHT(c) 2019 STMicroelectronics                                         #
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
# Maintenance appliction on a gateway.


# IMPORT

from __future__ import print_function
import sys
import os
import subprocess


# CONSTANTS

# Presentation message.
INTRO = """#################
# Gateway setup #
#################"""

# URIs.
HOME_PATH = '/home/root'
CONNECT_WIFI_PATH = HOME_PATH + '/connect_wifi.sh'
GATEWAY_RULES_PATH = '/etc/sysctl.d/98-gateway.conf'

# Configuring board.
CONNECT_WIFI = """#!/bin/sh

wpa_supplicant -i wlan0 -c /etc/wpa_supplicant.conf -B
dhclient wlan0
ifconfig
"""

# Python packages to install through pip tool.
PYTHON_PACKAGES_TO_INSTALL = 'AWSIoTPythonSDK wire-st-sdk edge-st-sdk'


# FUNCTIONS

# Main application.
def main(argv):

    try:
        # Printing presentation message.
        print('\n' + INTRO + '\n')

        # Configuring WiFi.
        fd = open(CONNECT_WIFI_PATH, 'w')
        fd.write(CONNECT_WIFI)
        fd.close()
        os.system('chmod 755 %s' % (CONNECT_WIFI_PATH))
        print('\n--> Connect the gateway to the Internet through an ethernet connection,\n' \
            'or configure a WiFi network and connect to it.')
        while True:
            choice = input('\n--> Do you want to configure a WiFi network? [Y/n] ' \
                ).lower()
            if choice == '' or choice == 'y' or choice == 'n':
                break
        if choice == '' or choice == 'y':
            wifi_ssid = input('Please enter your WiFi network\'s SSID: ')
            wifi_password = input('Please enter your WiFi network\'s password: ')
            os.system('wpa_passphrase %s %s > /etc/wpa_supplicant.conf' \
                % (wifi_ssid, wifi_password))
            print('\nWiFi network successfully configured. Run \'%s\' to connect.' \
                % (CONNECT_WIFI_PATH))
            while True:
                choice = input('\n--> Do you want to connect now? [Y/n] ').lower()
                if choice == '' or choice == 'y' or choice == 'n':
                    break
            if choice == '' or choice == 'y':
                try:
                    output = subprocess.check_output('%s | grep \'wlan\' -A1 | grep inet' \
                        % (CONNECT_WIFI_PATH),
                        stderr=subprocess.STDOUT, shell=True).decode('utf-8')
                except subprocess.CalledProcessError as e:
                    pass
                ip_address = output.split()[1].split(':')[1]
                if ip_address:
                    print('\nSuccessfully connected to %s with ip address %s.' \
                        % (wifi_ssid, ip_address))
                else:
                    print('\nImpossible to connect to %s.' % (wifi_ssid))

        # Installing Python packages.
        print('\n--> Installing Python packages...')
        os.system('pip3 install %s' % (PYTHON_PACKAGES_TO_INSTALL))

        # Adding user and group to the system.
        print('\n--> Configuring the system...')
        os.system('adduser --system ggc_user')
        os.system('addgroup --system ggc_group')

        # Enabling hardlink and softlink protection at operating system start-up.
        fd = open(GATEWAY_RULES_PATH, 'w')
        fd.write('fs.protected_hardlinks = 1\nfs.protected_symlinks = 1')
        fd.close()

        # Setup completed.
        print('\n--> Setup complete.\n')

    except KeyboardInterrupt:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)


if __name__ == "__main__":
        main(sys.argv[1:])
