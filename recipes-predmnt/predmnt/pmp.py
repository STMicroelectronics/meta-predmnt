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
import sys
import os
import time
import getopt
import json
import logging
from enum import Enum
import threading
import serial
from serial import SerialException
from serial import SerialTimeoutException
from datetime import datetime
import random

import wire_st_sdk.iolink.iolink_protocol as iolink_protocol
from wire_st_sdk.iolink.iolink_master import IOLinkMaster
from wire_st_sdk.iolink.iolink_master import IOLinkMasterListener
from wire_st_sdk.iolink.iolink_device import IOLinkDevice
from wire_st_sdk.utils.wire_st_exceptions import WireSTInvalidOperationException

from edge_st_sdk.aws.aws_greengrass import AWSGreengrass
from edge_st_sdk.aws.aws_greengrass import AWSGreengrassListener
from edge_st_sdk.aws.aws_client import AWSClient
from edge_st_sdk.edge_client import EdgeClientListener
from edge_st_sdk.utils.edge_st_exceptions import EdgeSTInvalidDataException
from edge_st_sdk.utils.edge_st_exceptions import EdgeSTInvalidOperationException


# CONSTANTS

# Usage message.
USAGE = """Usage:

python <application>.py [-h] -c <configuration_file>

"""

# Help message.
HELP = """-h, --help
    Shows these help information.
-c, --config-file
    Configuration file.
"""

# Presentation message.
INTRO = """####################################################
# Predictive Maintenance with Amazon AWS IoT cloud #
####################################################"""

# Timeouts.
SERIAL_PORT_TIMEOUT_s = 5
SHADOW_CALLBACK_TIMEOUT_s = 30
ENV_DATA_TIMEOUT_s = 30
INE_TDM_DATA_TIMEOUT_s = 30
INE_FDM_DATA_TIMEOUT_s = 30
ACO_DATA_TIMEOUT_s = 30
SHADOW_GET_TIMEOUT_s = 5

# MQTT QoS.
MQTT_QOS_0 = 0
MQTT_QOS_1 = 1

# Cloud's default MQTT Topics.
MQTT_AWS_HEADER_TOPIC = '$aws/things'
MQTT_AWS_GET_TOPIC = 'shadow/get'
MQTT_AWS_UPDATE_TOPIC = 'shadow/update'
MQTT_AWS_ACCEPTED_TOPIC = 'accepted'
MQTT_AWS_DELTA_TOPIC = 'delta'
MQTT_AWS_DOCUMENTS_TOPIC = 'documents'

# Custom MQTT Topics.
MQTT_HDR_TOPIC = "pm"
MQTT_CFG_TOPIC = "configuration"
MQTT_SNS_TOPIC = "sense"
MQTT_ENV_TOPIC = "environmental"
MQTT_INE_TOPIC = "inertial"
MQTT_ACO_TOPIC = "acoustic"
MQTT_TDM_TOPIC = "_tdm"
MQTT_FDM_TOPIC = "_fdm"

# Devices' certificates, private keys, and path on the Linux gateway.
CERTIF_EXT = ".cert.pem"
PRIV_K_EXT = ".private.key"
FDM_DUMPS_EXT = '_FDM.log'

# COnfiguration keywords for configuration file.
COMMENT_KEY = '#'
SERIAL_PORT_NAME_KEY = 'SERIAL_PORT_NAME'
SERIAL_PORT_BAUDRATE_bs_KEY = 'SERIAL_PORT_BAUDRATE_bs'
DEVICES_PATH_KEY = 'DEVICES_PATH'
ENDPOINT_KEY = 'ENDPOINT'
ROOT_CA_PATH_KEY = 'ROOT_CA_PATH'
FROM_IOLINK_KEY = 'FROM_IOLINK'
TO_CLOUD_KEY = 'TO_CLOUD'
USE_THREADS_KEY = 'USE_THREADS'
DUMP_FDM_KEY = 'DUMP_FDM'
DEVICE_KEY = 'DEVICE'
YES_KEY = 'YES'
NO_KEY = 'NO'

# Configured devices from configuration file.
CONFIGURED_DEVICES = {}

# Default configuration.
CONFIGURATION = {
    SERIAL_PORT_NAME_KEY: '/dev/ttyUSB0',
    SERIAL_PORT_BAUDRATE_bs_KEY: 230400,
    DEVICES_PATH_KEY: '/home/root/devices_pmp_aws',
    ENDPOINT_KEY: None,
    ROOT_CA_PATH_KEY: None,
    FROM_IOLINK_KEY: YES_KEY,
    TO_CLOUD_KEY: YES_KEY,
    USE_THREADS_KEY: YES_KEY,
    DUMP_FDM_KEY: 0
}


# SHADOW JSON SCHEMAS

# {
#   "desired": {
#     "welcome": "aws-iot"
#   },
#   "reported": {
#     "welcome": "aws-iot"
#   }
# }


# CLASSES

# Index of the handshake data.
class HsIndex (Enum):
    DEVICE_TYPE = 0
    FIRMWARE = 1
    FEATURES = 2


# Index of the environmental features.
class EnvIndex(Enum):
    PRESSURE = 0
    HUMIDITY = 1
    TEMPERATURE = 2


# Index of the time domain features.
class TdmIndex(Enum):
    RMS = 0
    PEAK = 1


# Index of the axes.
class AxesIndex(Enum):
    X = 0
    Y = 1
    Z = 2


#
# Implementation of the interface used by the IOLinkMaster class to notify the
# status of the connection.
#
class MyIOLinkMasterListener(IOLinkMasterListener):

    #
    # To be called whenever a masterboard changes its status.
    #
    # @param masterboard IOLinkMaster instance that has changed its status.
    # @param new_status New status.
    # @param old_status Old status.
    #
    def on_status_change(self, masterboard, new_status, old_status):
        print('Masterboard on port \"%s\" from \"%s\" to \"%s\".' %
            (masterboard.get_port().port, str(old_status), str(new_status)))

    #
    # To be called whenever a masterboard finds a new device connected.
    #
    # @param masterboard (IOLinkMaster): Masterboard that has found a new device.
    # @param device_id (str): New device found.
    # @param device_position (int): Position of the new device found.
    #
    def on_device_found(self, masterboard, device_id, device_position):
        print('Masterboard on port \"%s\" found device \"%s\" on position \"%d\".' %
            (masterboard.get_port().port, device_id, device_position))


#
# Implementation of the interface used by the EdgeClient class to notify that a
# client has updated its status.
#
class MyAWSGreengrassListener(AWSGreengrassListener):

    #
    # To be called whenever the AWS Greengrass service changes its status.
    #
    # @param aws_greengrass AWS Greengrass service that has changed its status.
    # @param new_status     New status.
    # @param old_status     Old status.
    #
    def on_status_change(self, aws_greengrass, new_status, old_status):
        print('AWS Greengrass service with endpoint \"%s\" from \"%s\" to \"%s\".' %
            (aws_greengrass.get_endpoint(), str(old_status), str(new_status)))


#
# Implementation of the interface used by the EdgeClient class to notify that a
# client has updated its status.
#
class MyClientListener(EdgeClientListener):

    #
    # To be called whenever a client changes its status.
    #
    # @param client     Client that has changed its status.
    # @param new_status New status.
    # @param old_status Old status.
    #
    def on_status_change(self, client, new_status, old_status):
        print('Client \"%s\" from \"%s\" to \"%s\".' %
            (client.get_name(), str(old_status), str(new_status)))


# FUNCTIONS

#
# Printing presentation message.
#
def print_intro():
    print('\n' + INTRO + '\n')

#
# Reading input.
#
def read_input(argv):
    # Reading in command-line parameters.
    try:
        opts, args = getopt.getopt(argv,
            "hc:",
            ["help", "config-file="])
        #if len(opts) == 0:
        #    raise getopt.GetoptError("No input parameters!")
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(USAGE + HELP)
                sys.exit(0)
            if opt in ("-c", "--config-file"):
                configuration_file = arg
    except getopt.GetoptError:
        print(USAGE + HELP)
        sys.exit(1)

    # Check configuration.
    if 'configuration_file' not in locals():
        print(USAGE + HELP)
        sys.exit(2)

    # Return configuration file.
    return configuration_file

#
# Reading configuration file.
#
def read_configuration(configuration_file):    
    # Reading configuration file.
    error = ''
    fd = open(configuration_file, 'r')
    for line in fd.readlines():
        if not line.startswith(COMMENT_KEY):
            tokens = line.strip().split()
            if tokens:
                if tokens[0] in CONFIGURATION:
                    CONFIGURATION[tokens[0]] = tokens[1]
                elif tokens[0] == DEVICE_KEY:
                    CONFIGURED_DEVICES[tokens[1]] = tokens[2]
    fd.close()

    # Checking configuration.
    for key in [FROM_IOLINK_KEY, TO_CLOUD_KEY, USE_THREADS_KEY]:
        if CONFIGURATION[key].upper() in [YES_KEY, NO_KEY]:
            CONFIGURATION[key] = True if CONFIGURATION[key] == YES_KEY \
                else False
        else:
            error += 'Wrong value for \"%s\" parameter in configuration file.\n' \
                % (key)
    if CONFIGURATION[TO_CLOUD_KEY]:
        if not CONFIGURATION[ENDPOINT_KEY]:
            error += 'Missing endpoint in configuration file.\n'
        if not CONFIGURATION[ROOT_CA_PATH_KEY]:
            error += 'Missing Root Certification Authority certificate in ' \
                'configuration file.\n'
    if error is not '':
        print('%sExiting...\n' % (error))
        sys.exit(2)

#
# Configure logging.
#
def configure_logging():
    logger = logging.getLogger("Demo")
    logger.setLevel(logging.ERROR)
    streamHandler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)

#
# Setting the flag for getting environmental data.
#
def set_env_flag(flag):
    global env_flags

    # Setting the flag for getting environmental data.
    env_flags[flag] = True

#
# Setting the flag for getting time domain data.
#
def set_tdm_flag(flag):
    global ine_tdm_flags

    # Setting the flag for getting time domain data.
    ine_tdm_flags[flag] = True

#
# Setting the flag for getting frequency domain data.
#
def set_fdm_flag(flag):
    global ine_fdm_flags

    # Setting the flag for getting frequency domain data.
    ine_fdm_flags[flag] = True

#
# Setting the flag for getting shadow state from AWS IoT.
#
def set_shadow_flag(flag):
    global shadow_flags

    # Setting the flag for getting shadow state from AWS IoT.
    shadow_flags[flag] = True

#
# Getting handshake data.
#
def get_handshake(device):
    data = []
    if isinstance(device, IOLinkDevice):
        data.append("STEVAL-IPD005V1")
        data.append(device.get_firmware())
        data.append(device.get_features())
    else:
        data.append("STEVAL-IPD005V1")
        data.append("Firmware Ver. 1.0.0")
        data.append(["Environmental", "Inertial_TDM", "Inertial_FDM"])
    return data

#
# Getting environmental data.
#
def get_env(device):
    if isinstance(device, IOLinkDevice):
        return device.get_env()
    else:
        return [round(1100.0 * random.random(), 3),
            round(100.0 * random.random(), 3),
            round(50.0 * random.random(), 3)]

#
# Getting time domain data.
#
def get_tdm(device):
    if isinstance(device, IOLinkDevice):
        return device.get_tdm()
    else:
        return [[round(10.0 * random.random(), 3),
            round(10.0 * random.random(), 3),
            round(10.0 * random.random(), 3)],
            [round(10.0 * random.random(), 3),
            round(10.0 * random.random(), 3),
            round(10.0 * random.random(), 3)]]

#
# Getting frequency domain data.
#
def get_fdm(device):
    if isinstance(device, IOLinkDevice):
        return device.get_fft()
    else:
        data = []
        for j in range(0, 1024):
            data.append([3.0 * j,
                round(10.0 * random.random(), 3),
                round(10.0 * random.random(), 3),
                round(10.0 * random.random(), 3)])
        return data

#
# Publishing handshake data.
#
def publish_handshake(data, client):
    # Getting a JSON representation of the message to publish.
    state_json = {
        "state": {
            "reported": {
                "Device_Type": str(data[HsIndex.DEVICE_TYPE.value]), 
                "Firmware": str(data[HsIndex.FIRMWARE.value]), 
                "Features": data[HsIndex.FEATURES.value]
            }
        }
    }

    # Udating shadow state.
    state_json_str = json.dumps(state_json, sort_keys=True)
    print('[%s] (%s): %s' % \
        (client.get_name(), datetime.now().time(), state_json_str))
    client.update_shadow_state(
        state_json_str,
        custom_shadow_callback_update,
        SHADOW_CALLBACK_TIMEOUT_s)

#
# Publishing Environmental data.
#
def publish_env(data, client):
    # Getting a JSON representation of the message to publish.
    data_json = {
        "Pressure": data[EnvIndex.PRESSURE.value], 
        "Humidity": data[EnvIndex.HUMIDITY.value], 
        "Temperature": data[EnvIndex.TEMPERATURE.value]
    }

    # Publishing the message.
    data_json_str = json.dumps(data_json, sort_keys=True)
    client_name = client.get_name() if isinstance(client, AWSClient) \
        else client
    print('[%s] (%s): %s' % \
        (client_name, datetime.now().time(), data_json_str))
    if isinstance(client, AWSClient):
        topic = MQTT_HDR_TOPIC + "/" + client_name + "/" \
            + MQTT_SNS_TOPIC + "/" + MQTT_ENV_TOPIC
        client.publish(topic, data_json_str, MQTT_QOS_0)

#
# Publishing Inertial Time Domain data.
#
def publish_ine_tdm(data, client):
    # Getting a JSON representation of the message to publish.
    data_json = {
        "RMS_Speed": data[TdmIndex.RMS.value],
        "Peak_Acceleration": data[TdmIndex.PEAK.value]
    }

    # Publishing the message.
    data_json_str = json.dumps(data_json, sort_keys=True)
    client_name = client.get_name() if isinstance(client, AWSClient) \
        else client
    print('[%s] (%s): %s' % \
        (client_name, datetime.now().time(), data_json_str))
    if isinstance(client, AWSClient):
        topic = MQTT_HDR_TOPIC + "/" + client_name + "/" \
            + MQTT_SNS_TOPIC + "/" + MQTT_INE_TOPIC + MQTT_TDM_TOPIC
        client.publish(topic, data_json_str, MQTT_QOS_0)

#
# Publishing Inertial Frequency Domain data.
#
def publish_ine_fdm(data, client):
    global fdm_dumped

    # Getting a JSON representation of the message to publish.
    data_json = {
        "Ine_FFT": data
    }

    # Publishing the message.
    data_json_tmp = {
        "Ine_FFT": "[" + str(len(data)) + "]"
    }
    data_json_tmp_str = json.dumps(data_json_tmp, sort_keys=True)
    client_name = client.get_name() if isinstance(client, AWSClient) \
        else client
    print('[%s] (%s): %s' % \
        (client_name, datetime.now().time(), data_json_tmp_str))
    data_json_str = json.dumps(data_json, sort_keys=True)
    if isinstance(client, AWSClient):
        topic = MQTT_HDR_TOPIC + "/" + client_name + "/" \
            + MQTT_SNS_TOPIC + "/" + MQTT_INE_TOPIC + MQTT_FDM_TOPIC
        client.publish(topic, data_json_str, MQTT_QOS_0)
    if fdm_dumped[client_name] > 0:
        dump_ine_fdm(client_name, data_json_str)

#
# Dumping Inertial Frequency Domain data.
#
def dump_ine_fdm(device_name, data_json_str):
    global fdm_dumped

    data_json_str = data_json_str.replace(': [[', ': [\r\n[')
    data_json_str = data_json_str.replace('], [', '], \r\n[')
    data_json_str = data_json_str.replace(']]}', ']\r\n]}\r\n')
    fd = open(device_name + FDM_DUMPS_EXT, 'a')
    fd.write(data_json_str)
    fd.close()
    fdm_dumped[device_name] -= 1
    end = 0
    for device_name in fdm_dumped:
        end += fdm_dumped[device_name]
    if not end:
        print('\nDumping samples completed. Exiting...\n')
        sys.exit(0)

#
# Initializing dumps.
#
def initialize_dumps(devices, dumps=0):
    global fdm_dumped
    fdm_dumped = {}
    for device in devices:
        device_name = device.get_name() if isinstance(device, IOLinkDevice) \
            else device
        fdm_dumped[device_name] = dumps


# SHADOW DEVICES' CALLBACKS

#
# Custom shadow callback for "get()" operations.
#
def custom_shadow_callback_get(payload, response_status, token):
    # "payload" is a JSON string ready to be parsed using "json.loads()" both in
    # both Python 2.x and Python 3.x
    print("Get request with token \"" + token + "\" " + response_status)
    #if response_status == "accepted":
    #state_json_str = json.loads(payload)
    #print(state_json_str)

#
# Custom shadow callback for "update()" operations.
#
def custom_shadow_callback_update(payload, response_status, token):
    # "payload" is a JSON string ready to be parsed using "json.loads()" both in
    # both Python 2.x and Python 3.x
    print("Update request with token \"" + token + "\" " + response_status)
    #if response_status == "accepted":
    #state_json_str = json.loads(payload)
    #print(state_json_str)

#
# Custom shadow callback for "update()" operations.
#
# def custom_shadow_callback_update_delta(payload, response_status, token):
#     # "payload" is a JSON string ready to be parsed using "json.loads()" both in
#     # both Python 2.x and Python 3.x
#     print("Update-Delta request with token \"" + token + "\" " + response_status)
#     #if response_status == "accepted":
#     state_json_str = json.loads(payload)
#     print(state_json_str)

#
# Custom shadow callback for "delete()" operations.
#
def custom_shadow_callback_delete(payload, response_status, token):
    # "payload" is a JSON string ready to be parsed using "json.loads()" both in
    # both Python 2.x and Python 3.x
    print("Delete request with token \"" + token + "\" " + response_status)
    #if response_status == "accepted":
    #    state_json_str = json.loads(payload)


#CLASSES

#
# Setting flag.
#
class FlagThread(threading.Thread):

    #
    # Constructor.
    #
    def __init__(self, function, flag, timeout):
        threading.Thread.__init__(self)
        self._function = function
        self._flag = flag
        self._timeout = timeout
        self.daemon = True

    #
    # Run the thread.
    #
    def run(self):
        while True:
            self._function(self._flag)
            time.sleep(self._timeout)


# MAIN APPLICATION

#
# Main application.
#
def main(argv):

    # Global variables.
    global env_flags, ine_tdm_flags, ine_fdm_flags, shadow_flags

    try:
        # Configure logging.
        configure_logging()

        # Printing intro.
        print_intro()

        # Reading input.
        configuration_file = read_input(argv)

        # Reading configuration file.
        read_configuration(configuration_file)

        # IO-LINK CONFIGURATION.

        devices = []
        if CONFIGURATION[FROM_IOLINK_KEY]:
            # Initializing Serial Port.
            serial_port = serial.Serial()
            serial_port.port = CONFIGURATION[SERIAL_PORT_NAME_KEY]
            serial_port.baudrate = int(CONFIGURATION[SERIAL_PORT_BAUDRATE_bs_KEY])
            serial_port.parity = serial.PARITY_NONE
            serial_port.stopbits = serial.STOPBITS_ONE
            serial_port.bytesize = serial.EIGHTBITS
            serial_port.timeout = SERIAL_PORT_TIMEOUT_s
            serial_port.write_timeout = None

            # Initializing an IO-Link Masterboard and connecting it to the host.
            print('\nInitializing Masterboard on port \"%s\" with a baud rate of ' \
                '\"%d\" [b/s]...' % (serial_port.port, serial_port.baudrate))
            master = IOLinkMaster(serial_port)
            master_listener = MyIOLinkMasterListener()
            master.add_listener(master_listener)
            status = master.connect()

            # Initializing IO-Link Devices.
            print('\nInitializing IO-Link Devices...')
            for device_name in CONFIGURED_DEVICES:
                device_position = int(CONFIGURED_DEVICES[device_name])
                devices.append(master.get_device_by_position(
                    device_position, device_name))
                print('Device \"%s\" on position \"%d\" initialized.' % \
                    (device_name, device_position))

            # Checking setup.
            for device in devices:
                if not device:
                    print('IO-Link setup incomplete. Exiting...\n')
                    sys.exit(0)

            # IO-Link setup complete.
            print('\nIO-Link setup complete.\n')

            # Setting devices' parameters.
            # sze = iolink_protocol.SZE.SZE_1024
            # for device in devices:
            #     print('Device %d:' % (device.get_position()))
            #     print('\tSetting SZE to %s...' % (sze.value), end='')
            #     sys.stdout.flush()
            #     print('Done' if device.set_sze(sze) else 'Error')
        else:
            for device_name in CONFIGURED_DEVICES:
                devices.append(device_name)


        # CLOUD CONFIGURATION.
        clients = []
        if CONFIGURATION[TO_CLOUD_KEY]:
            # Initializing Edge Computing.
            print('\nInitializing Edge Computing...\n')
            edge = AWSGreengrass(
                CONFIGURATION[ENDPOINT_KEY],
                CONFIGURATION[ROOT_CA_PATH_KEY])
            edge.add_listener(MyAWSGreengrassListener())

            # Initializing AWS MQTT clients.
            for device_name in CONFIGURED_DEVICES:
                clients.append(edge.get_client(
                    device_name,
                    CONFIGURATION['DEVICES_PATH'] \
                    + '//' + device_name + CERTIF_EXT,
                    CONFIGURATION['DEVICES_PATH'] \
                    + '//' + device_name + PRIV_K_EXT))

            # Connecting clients to the cloud.
            for client in clients:
                client.add_listener(MyClientListener())
                if not client.connect():
                    print('Client \"%s\" cannot connect to core.\n' \
                        'AWS setup incomplete. Exiting...\n' % \
                        (client.get_name()))
                    sys.exit(0)

            # Sending handshake information.
            print('\nSending handshake information...\n')
            for i in range(0, len(devices)):
                # Getting data.
                data = get_handshake(devices[i])

                # Publishing data.
                publish_handshake(data, clients[i])

            # Subscribing to Cloud's default topics.
            for client in clients:
                client.subscribe(
                    MQTT_AWS_HEADER_TOPIC + "/"
                    + client.get_name() + "/"
                    + MQTT_AWS_GET_TOPIC,
                    MQTT_QOS_1,
                    custom_shadow_callback_get)
                client.subscribe(
                    MQTT_AWS_HEADER_TOPIC + "/"
                    + client.get_name() + "/"
                    + MQTT_AWS_UPDATE_TOPIC,
                    MQTT_QOS_1,
                    custom_shadow_callback_update)
                # client.subscribe(
                #     MQTT_AWS_HEADER_TOPIC + "/"
                #     + client.get_name() + "/"
                #     + MQTT_AWS_UPDATE_TOPIC + "/"
                #     #+ MQTT_AWS_ACCEPTED_TOPIC, 
                #     #+ MQTT_AWS_DOCUMENTS_TOPIC,
                #     + MQTT_AWS_DELTA_TOPIC,
                #     MQTT_QOS_1,
                #     custom_shadow_callback_update_delta)
            
            # Edge Computing Initialized.
            print('\nEdge Computing setup complete.\n')
        else:
            for device_name in CONFIGURED_DEVICES:
                clients.append(device_name)


        # GETTING DATA AND PUBLISHING.

        if CONFIGURATION[USE_THREADS_KEY]:
            # Sensors' flags.
            env_flags = [False] * len(devices)
            ine_tdm_flags = [False] * len(devices)
            ine_fdm_flags = [False] * len(devices)

            # Shadow devices' flags.
            shadow_flags = [False] * len(devices)

            # Starting threads.
            for i in range(0, len(devices)):
                FlagThread(set_env_flag, i, ENV_DATA_TIMEOUT_s).start()
                FlagThread(set_tdm_flag, i, INE_TDM_DATA_TIMEOUT_s).start()
                FlagThread(set_fdm_flag, i, INE_FDM_DATA_TIMEOUT_s).start()
                #if CONFIGURATION[TO_CLOUD_KEY]:
                #    FlagThread(set_shadow_flag, i, SHADOW_GET_TIMEOUT_s).start()

            # Measurements.
            initialize_dumps(devices, int(CONFIGURATION[DUMP_FDM_KEY]))

            # Demo running.
            print('\nDemo running...\n')

            # Infinite loop.
            while True:
                for i in range(0, len(devices)):
                    if env_flags[i]:
                        # Getting data.
                        data = get_env(devices[i])

                        # Publishing data.
                        publish_env(data, clients[i])

                        # Resetting flag.
                        env_flags[i] = False

                    elif ine_tdm_flags[i]:
                        # Getting data.
                        data = get_tdm(devices[i])

                        # Publishing data.
                        publish_ine_tdm(data, clients[i])

                        # Resetting flag.
                        ine_tdm_flags[i] = False

                    elif ine_fdm_flags[i]:
                        # Getting data.
                        data = get_fdm(devices[i])

                        # Publishing data.
                        publish_ine_fdm(data, clients[i])

                        # Resetting flag.
                        ine_fdm_flags[i] = False

                    # elif shadow_flags[i] and CONFIGURATION[TO_CLOUD_KEY]:
                    #     # Getting shadow's state.
                    #     clients[i].get_shadow_state(custom_shadow_callback_get, SHADOW_CALLBACK_TIMEOUT_s)

                    #     # Resetting flag.
                    #     shadow_flags[i] = False

        else:
            # Measurements.
            initialize_dumps(devices, int(CONFIGURATION[DUMP_FDM_KEY]))

            # Demo running.
            print('\nDemo running...\n')

            # Infinite loop.
            while True:
                for i in range(0, len(devices)):
                    # Getting data.
                    data = get_env(devices[i])

                    # Publishing data.
                    publish_env(data, clients[i])

                    # Getting data.
                    data = get_tdm(devices[i])

                    # Publishing data.
                    publish_ine_tdm(data, clients[i])

                    # Getting data.
                    data = get_fdm(devices[i])

                    # Publishing data.
                    publish_ine_fdm(data, clients[i])

    except (EdgeSTInvalidDataException, EdgeSTInvalidOperationException, \
        WireSTInvalidOperationException, SerialException, SerialTimeoutException, \
        ValueError) as e:
        print(e)
        print('\nExiting...\n')
        sys.exit(0)
    except KeyboardInterrupt:
        try:
            print('\nExiting...\n')
            sys.exit(0)
        except SystemExit:
            os._exit(0)


if __name__ == "__main__":
    main(sys.argv[1:])
