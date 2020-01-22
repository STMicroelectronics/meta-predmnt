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

from utils import gtk_utils
import pmp_definitions


# CONSTANTS

# AWS Greengrass.
GREENGRASS_GROUP_PATH = pmp_definitions.GREENGRASS_PATH \
    + '/ggc/deployment/group/group.json'
RESTART_GREENGRASS_COMMAND = pmp_definitions.GREENGRASS_PATH \
    + '/ggc/core/greengrassd restart'
RESTART_GREENGRASS_OUTPUT_PATH = pmp_definitions.HOME_PATH \
    + '/greengrass_output'
RESTART_GREENGRASS_OK = 'Greengrass successfully started'


#FUNCTIONS

#
# Configure edge gateway for AWS.
#
def configure_edge_gateway_aws(edge_gateway_path, textbuffer=None):
    edge_gateway_basename = os.path.basename(edge_gateway_path)
    try:
        command = \
            'cd %s && ' \
            'rm -rf certs config && ' \
            'cp %s . && ' \
            'unzip -o %s && ' \
            'rm -rf %s 2>&1' % \
            (pmp_definitions.GREENGRASS_PATH, edge_gateway_path,
                edge_gateway_basename, edge_gateway_basename)
        output = subprocess.check_output(command,
            stderr=subprocess.STDOUT, shell=True).decode('utf-8')
        if textbuffer:
            gtk_utils.write_to_buffer(textbuffer, output)
    except subprocess.CalledProcessError as e:
        pass
    endpoint = json.load(open(pmp_definitions.GREENGRASS_CONFIG_PATH))["coreThing"]["iotHost"]

#
# Configure devices for AWS.
#
def configure_devices_aws(devices_dict, textbuffer=None):
    try:
        with open(pmp_definitions.PMP_CONFIGURATION_PATH, 'r') as fp:
            pmp_configuration_json = json.load(fp)
        device_certificates_path = \
            pmp_configuration_json["setup"]["device_certificates_path"]
        command = \
            'rm -rf %s && ' \
            'mkdir -p %s 2>&1' % \
            (device_certificates_path, device_certificates_path)
        output = subprocess.check_output(command,
            stderr=subprocess.STDOUT, shell=True).decode('utf-8')
        if textbuffer:
            gtk_utils.write_to_buffer(textbuffer, output)
    except subprocess.CalledProcessError as e:
        pass
    root_ca_path = json.load(open(pmp_definitions.GREENGRASS_CONFIG_PATH))["coreThing"]["caPath"]
    for position in devices_dict:
        device_path = devices_dict[position]
        device_basename = os.path.basename(device_path)
        try:
            command = \
                'cd %s && ' \
                'cp %s . && ' \
                'unzip -o %s && ' \
                'rm -rf %s %s 2>&1' % \
                (device_certificates_path, device_path,
                    device_basename, device_basename, root_ca_path)
            output = subprocess.check_output(command,
                stderr=subprocess.STDOUT, shell=True).decode('utf-8')
            if textbuffer:
                gtk_utils.write_to_buffer(textbuffer, output)
        except subprocess.CalledProcessError as e:
            pass
        with open(pmp_definitions.PMP_CONFIGURATION_PATH, 'r') as fp:
            pmp_configuration_json = json.load(fp)
        device_dict = {}
        device_dict["name"] = device_basename[:device_basename.find('.')]
        device_dict["position"] = int(position.split(' ')[1])
        pmp_configuration_json["setup"]["devices"].append(device_dict)
        with open(pmp_definitions.PMP_CONFIGURATION_PATH, 'w') as fp:
            json.dump(pmp_configuration_json, fp)

#
# Restart AWS Greengrass.
#
def restart_aws_greengrass():
    os.system('%s > %s' % \
        (RESTART_GREENGRASS_COMMAND, RESTART_GREENGRASS_OUTPUT_PATH))
    while True:
        try:
            output = subprocess.check_output('cat %s' \
                % (RESTART_GREENGRASS_OUTPUT_PATH), \
                stderr=subprocess.STDOUT, shell=True).decode('utf-8')
            if RESTART_GREENGRASS_OK in output:
                os.system('rm -rf %s' % \
                    (RESTART_GREENGRASS_OUTPUT_PATH))
                #print(RESTART_GREENGRASS_OK)
                break
        except subprocess.CalledProcessError as e:
            pass

#
# Wait for deployment from the AWS cloud.
#
def wait_for_aws_deployment():
    #print('Waiting for deployment...')
    group_date_orig = group_date_new = subprocess.check_output('stat -c %%y %s' \
        % (GREENGRASS_GROUP_PATH), \
        stderr=subprocess.STDOUT, shell=True).decode('utf-8')
    while group_date_orig == group_date_new:
        try:
            group_date_new = subprocess.check_output('stat -c %%y %s' \
                % (GREENGRASS_GROUP_PATH), \
                stderr=subprocess.STDOUT, shell=True).decode('utf-8')
        except subprocess.CalledProcessError as e:
            pass
    #print('Deployment successfully completed!')
