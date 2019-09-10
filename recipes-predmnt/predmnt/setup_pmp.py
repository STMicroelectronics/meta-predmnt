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
# This application helps configuring the Predictive Maintenance appliction on a
# gateway.


# IMPORT

from __future__ import print_function
import sys
import os
import subprocess
import time
import json


# CONSTANTS

# Presentation message.
INTRO = """#####################################################
# Predictive Maintenance Platform Application setup #
#####################################################"""

# URIs.
HOME_PATH = '/home/root'
PREDMNT_PATH = '/usr/local/predmnt'
GREENGRASS_PATH = '/greengrass'
GREENGRASS_CONFIG_PATH = GREENGRASS_PATH + '/config/config.json'
GREENGRASS_GROUP_PATH = GREENGRASS_PATH + '/ggc/deployment/group/group.json'
RESTART_GREENGRASS_OUTPUT_PATH = PREDMNT_PATH + '/greengrass_output'
PMP_CONFIGURATION_PATH = PREDMNT_PATH + '/pmp.cfg'
PMP_START_APPLICATION_PATH = PREDMNT_PATH + '/start_pmp.sh'
MOUNT_POINT_PATH = '/mnt/usb'

# Configuring board.
CONNECT_WIFI = """#!/bin/sh

wpa_supplicant -i wlan0 -c /etc/wpa_supplicant.conf -B
dhclient wlan0
ifconfig
"""

# Python packages to install through pip tool.
PYTHON_PACKAGES_TO_INSTALL = 'AWSIoTPythonSDK wire-st-sdk edge-st-sdk'

# Command to restart Greengrass.
RESTART_GREENGRASS_COMMAND = '/greengrass/ggc/core/greengrassd restart'
RESTART_GREENGRASS_OK = 'Greengrass successfully started'

# PMP Configuration File.
PMP_CONFIGURATION_FILE = """# CONFIGURATION FILE FOR PREDICTIVE MAINTENANCE PLATFORM APPLICATION.

# IO-Link masterboard configuration (name and baudrate in [bit/second]).
SERIAL_PORT_NAME            /dev/ttyUSB0
SERIAL_PORT_BAUDRATE_bs     230400

# Connects to a real IO-Link masterboard, otherwise simulates data (YES/NO).
FROM_IOLINK                 YES

# Sends data to the cloud (YES/NO).
TO_CLOUD                    YES

# Uses threads when polling sensors (YES/NO).
USE_THREADS                 YES

# Dumps the given number of FDM samples to a "<device-name>_FDM.log" file for
# each device, then exits.
DUMP_FDM                    0

# Root Certification Authority certificate path on the gateway.
ROOT_CA_PATH                /greengrass/certs/root.ca.pem

# Path of the devices credentials on the gateway.
DEVICES_PATH                /usr/local/predmnt/devices_pmp_aws

# Amazon IoT custom endpoint.
ENDPOINT                    <ENDPOINT>

# Device(s) name on the cloud and position on the IO-Link masterboard.
DEVICE                      <DEVICE_NAME> <DEVICE_POSITION>
"""


# FUNCTIONS

# Main application.
def main(argv):

    try:
        # Printing presentation message.
        print('\n' + INTRO + '\n')

        # Gateway configuration.
        with open(PMP_CONFIGURATION_PATH, 'w') as file:
            file.write(PMP_CONFIGURATION_FILE)
        print('\n--> Configuring edge gateway and devices\n' \
            '1) Log in to the dashboard\n' \
            '2) Configure your devices and copy the credentials (zip files)\n' \
            '   to the root of a USB key\n' \
            '3) Configure your edge gateway and copy the credentials (zip file)\n' \
            '   to the root of the USB key\n'
            '4) Assign the devices to the edge gateway\n'
            '5) Plug the USB key into the gateway\n')
        #os.system('fdisk -l | grep sda | awk \'{ if ( $1 ~ "/dev/sda") { print $1 } }\'')
        while True:
            try:
                output = subprocess.check_output('ls /dev/sd*',
                    stderr=subprocess.STDOUT, shell=True).decode('utf-8').split('\n')
                device_point_path = max(output, key=len)
                if len(device_point_path) > 8:
                    break
            except subprocess.CalledProcessError as e:
                pass
        os.system(
            'mkdir -p %s && ' \
            'mount %s %s ' % \
            (MOUNT_POINT_PATH, device_point_path, MOUNT_POINT_PATH))
        edge_gateway = input('Enter the name of the edge gateway you want to ' \
            'configure (case-sensitive): ')
        os.system(
            'cd %s && ' \
            'rm -rf certs config && ' \
            'cp %s/%s.zip . && ' \
            'unzip %s.zip && ' \
            'rm -rf %s.zip' % \
            (GREENGRASS_PATH, MOUNT_POINT_PATH, edge_gateway, \
                edge_gateway, edge_gateway))
        root_ca_path = json.load(open(GREENGRASS_CONFIG_PATH))['coreThing']['caPath']
        endpoint = json.load(open(GREENGRASS_CONFIG_PATH))['coreThing']['iotHost']
        with open(PMP_CONFIGURATION_PATH, 'r') as file:
            data = file.read()
        data = data.replace('<ENDPOINT>', endpoint)
        with open(PMP_CONFIGURATION_PATH, 'w') as file:
            file.write(data)
        print('\nEdge gateway %s successfully configured.' % (edge_gateway))

        # Devices configuration.
        try:
            devices_path = subprocess.check_output('cat %s | grep DEVICES_PATH' \
                % (PMP_CONFIGURATION_PATH), \
                stderr=subprocess.STDOUT, shell=True).decode('utf-8').split()[1]
        except subprocess.CalledProcessError as e:
            pass
        os.system(
            'mkdir -p %s && ' \
            'rm -rf %s/*' % \
            (devices_path, devices_path))
        device_names = []
        device_positions = []
        while True:
            while True:
                device_name = input('\nEnter the name of the device you want to ' \
                    'configure (case-sensitive): ')
                if not device_name in device_names:
                    device_names.append(device_name)
                    break
                else:
                    print('Device name %s already ' \
                        'in use. Please try again.' % (device_name))
            while True:
                device_position = int(input('Device position [1..4]: '))
                if device_position in range(1, 5) \
                    and not device_position in device_positions:
                    device_positions.append(device_position)
                    break
                else:
                    print('Device position %d out of range or already ' \
                        'in use. Please try again.' % (device_position))
            os.system(
                'cd %s && ' \
                'cp %s/%s.zip . && ' \
                'unzip %s.zip && ' \
                'rm -rf %s.zip %s' % \
                (devices_path, MOUNT_POINT_PATH, \
                    device_name, device_name, device_name, root_ca_path))
            with open(PMP_CONFIGURATION_PATH, 'r') as file:
                data = file.read()
            data = data.replace('<DEVICE_NAME> <DEVICE_POSITION>',
                '%s %d\nDEVICE                      <DEVICE_NAME> <DEVICE_POSITION>' \
                % (device_name, device_position))
            with open(PMP_CONFIGURATION_PATH, 'w') as file:
                file.write(data)
            print('\nDevice %s successfully configured at position %d.' \
                % (device_name, device_position))
            while True:
                choice = input('\n--> Do you want to configure another device? [Y/n] ' \
                    ).lower()
                if choice == '' or choice == 'y' or choice == 'n':
                    break
            if choice == 'n':
                with open(PMP_CONFIGURATION_PATH, 'r') as file:
                    data = file.read()
                data = data.replace(
                    '\nDEVICE                      <DEVICE_NAME> <DEVICE_POSITION>',
                    '')
                with open(PMP_CONFIGURATION_PATH, 'w') as file:
                    file.write(data)
                os.system(
                    'umount %s &&' \
                    'rm -rf %s' % \
                    (device_point_path, MOUNT_POINT_PATH))
                break

        # Restarting Greengrass.
        print('\n--> Restarting Greengrass...')
        os.system('%s > %s' % \
            (RESTART_GREENGRASS_COMMAND, RESTART_GREENGRASS_OUTPUT_PATH))
        while True:
            try:
                output = subprocess.check_output('cat %s' \
                    % (RESTART_GREENGRASS_OUTPUT_PATH), \
                    stderr=subprocess.STDOUT, shell=True).decode('utf-8')
                if RESTART_GREENGRASS_OK in output:
                    print('\n%s.' % (RESTART_GREENGRASS_OK))
                    os.system('rm -rf %s' % \
                    (RESTART_GREENGRASS_OUTPUT_PATH))
                    break
            except subprocess.CalledProcessError as e:
                pass

        # Deployment.
        print('\n--> Unplug the USB key, come back to the dashboard and deploy\n' \
            '    the solution to the gateway.')
        while True:
            try:
                output = subprocess.check_output('cat %s' \
                    % (GREENGRASS_GROUP_PATH), \
                    stderr=subprocess.STDOUT, shell=True).decode('utf-8')
                core = '%s_Core' % (edge_gateway)
                if core in output:
                    print('\nDeployment successfully done.')
                    break
            except subprocess.CalledProcessError as e:
                pass

        # Setup completed.
        print('\n--> Your configuration is complete (see \"%s\").' \
            % (PMP_CONFIGURATION_PATH))

        print('\n--> Start the application by running:\n' \
            '      %s\n' % (PMP_START_APPLICATION_PATH))

    except KeyboardInterrupt:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)


if __name__ == "__main__":
        main(sys.argv[1:])
