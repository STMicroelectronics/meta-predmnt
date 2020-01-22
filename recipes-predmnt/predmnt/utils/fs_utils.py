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
import json

import pmp_definitions


# CONSTANTS

# USB Key.
MAXIMUM_MOUNT_TRIALS = 10
MOUNT_POINT_PATH = '/media/usb'

# WiFi.
CONNECT_WIFI_PATH = pmp_definitions.HOME_PATH + '/connect_wifi.sh'
DISCONNECT_WIFI_PATH = pmp_definitions.HOME_PATH + '/disconnect_wifi.sh'
CONFIGURATION_WIFI_PATH = '/etc/wpa_supplicant.conf'
CONNECT_WIFI = \
"""#!/bin/sh

wpa_supplicant -B -i wlan0 -c %s
dhclient wlan0
ifconfig
"""
DISCONNECT_WIFI = \
"""#!/bin/sh

dhclient -r wlan0
killall wpa_supplicant
"""


# FUNCTIONS

#
# Create file.
#
def create_file(file_path, file_content):
    with open(file_path, 'w') as fp:
        fp.write(file_content)

#
# Create configuration file from json object.
#
def create_file_from_json(file_path, json_object):
    with open(file_path, 'w') as fp:
        json.dump(json_object, fp, sort_keys=True)

#
# Mount the usb key.
#
def mount_usb_key():
    trials = MAXIMUM_MOUNT_TRIALS
    device_point_path = None
    try:
        output = subprocess.check_output('mount | grep %s' % \
            (MOUNT_POINT_PATH),
            stderr=subprocess.STDOUT, shell=True).decode('utf-8').split('\n')
        if output:
            return
    except subprocess.CalledProcessError as e:
        while trials:
            try:
                output = subprocess.check_output('ls /dev/sd*',
                    stderr=subprocess.STDOUT, shell=True).decode('utf-8').split('\n')
                device_point_path = max(output, key=len)
                if device_point_path and len(device_point_path) > 8:
                    break
            except subprocess.CalledProcessError as e:
                trials -= 1
                pass
        if device_point_path:
            if not os.path.exists(MOUNT_POINT_PATH):
                os.system('mkdir -p %s' % (MOUNT_POINT_PATH))
            try:
                subprocess.check_output('mount | grep %s' % \
                    (device_point_path),
                    stderr=subprocess.STDOUT, shell=True).decode('utf-8').split('\n')
            except subprocess.CalledProcessError as e:
                os.system('mount %s %s' % (device_point_path, MOUNT_POINT_PATH))

#
# Unmount the usb key.
#
def unmount_usb_key():
    os.system(
        'umount %s &&' \
        'rm -rf %s' % \
        (MOUNT_POINT_PATH, MOUNT_POINT_PATH))

#
# Create scripts to connect/disconnect to/from a WiFi network.
#
def create_wifi_scripts(connection_ssid, connection_password):
    os.system('wpa_passphrase %s %s > /etc/wpa_supplicant.conf' \
        % (connection_ssid, connection_password))
    fd = open(CONNECT_WIFI_PATH, 'w')
    fd.write(CONNECT_WIFI % (CONFIGURATION_WIFI_PATH))
    fd.close()
    os.system('chmod 755 %s' % (CONNECT_WIFI_PATH))
    fd = open(DISCONNECT_WIFI_PATH, 'w')
    fd.write(DISCONNECT_WIFI)
    fd.close()
    os.system('chmod 755 %s' % (DISCONNECT_WIFI_PATH))
