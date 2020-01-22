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
import os
import sys
import signal
import getopt
import json
import logging
from enum import Enum
import threading
import serial
from serial import SerialException
from serial import SerialTimeoutException
import random
import time
#from datetime import datetime

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

import pmp_definitions


# CONSTANTS

# Usage message.
USAGE = """Usage:

python3 pmp.py [-h] -c <configuration_file>

"""

# Help message.
HELP = """-h, --help
    Shows these help information.
-c, --config-file
    Configuration file (.json).
"""

# Presentation message.
INTRO = """####################################################
# Predictive Maintenance with Amazon AWS IoT cloud #
####################################################"""

# Devices' certificates, private keys, and path on the Linux gateway.
CERTIF_EXT = ".cert.pem"
PRIV_K_EXT = ".private.key"
DUMP_EXT = ".log"

# Timeouts.
SERIAL_PORT_TIMEOUT_s = 5
SHADOW_CALLBACK_TIMEOUT_s = 30
ENV_DATA_TIMEOUT_s = 30
INE_TDM_DATA_TIMEOUT_s = 30
INE_FDM_DATA_TIMEOUT_s = 5
ACO_DATA_TIMEOUT_s = 30
SHADOW_GET_TIMEOUT_s = 5


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


#
# Main application class.
#
class PMP():

    #
    # Constructor.
    #
    def __init__(self, argv):
        self._argv = argv

    #
    # Start the main PMP application.
    #
    def start(self):
        try:
            # Configure logging.
            self.configure_logging()

            # Printing intro.
            self.print_intro()

            # Reading input.
            configuration_file = self.read_input(self._argv)

            # Reading configuration file.
            self.read_configuration(configuration_file)


            # IO-LINK CONFIGURATION.

            devices = []
            if self.configuration["setup"]["use_sensors"]:
                # Initializing Serial Port.
                serial_port = serial.Serial()
                serial_port.port = self.configuration["serial_port"]["name"]
                serial_port.baudrate = \
                    self.configuration["serial_port"]["baudrate_bits_per_second"]
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
                for device in self.configuration["setup"]["devices"]:
                    device_name = device["name"]
                    device_position = device["position"]
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
                for device in self.configuration["setup"]["devices"]:
                    device_name = device["name"]
                    devices.append(device_name)


            # CLOUD CONFIGURATION.

            clients = []
            if self.configuration["setup"]["use_cloud"]:
                # Initializing Edge Computing.
                print('\nInitializing Edge Computing...\n')
                edge = AWSGreengrass(
                    self.endpoint,
                    self.root_ca_path)
                edge.add_listener(MyAWSGreengrassListener())

                # Initializing AWS MQTT clients.
                for device in self.configuration["setup"]["devices"]:
                    device_name = device["name"]
                    clients.append(edge.get_client(
                        device_name,
                        self.configuration["setup"]["device_certificates_path"] \
                        + '/' + device_name + CERTIF_EXT,
                        self.configuration["setup"]["device_certificates_path"] \
                        + '/' + device_name + PRIV_K_EXT))

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
                    data = self.get_handshake(devices[i])

                    # Publishing data.
                    self.publish_handshake(data, clients[i])

                # Subscribing to Cloud's default topics.
                for client in clients:
                    client.subscribe(
                        pmp_definitions.MQTT_AWS_HEADER_TOPIC + "/"
                        + client.get_name() + "/"
                        + pmp_definitions.MQTT_AWS_GET_TOPIC,
                        pmp_definitions.MQTT_QOS_1,
                        self.on_shadow_get_callback)
                    client.subscribe(
                        pmp_definitions.MQTT_AWS_HEADER_TOPIC + "/"
                        + client.get_name() + "/"
                        + pmp_definitions.MQTT_AWS_UPDATE_TOPIC,
                        pmp_definitions.MQTT_QOS_1,
                        self.on_shadow_update_callback)
                    # client.subscribe(
                    #     pmp_definitions.MQTT_AWS_HEADER_TOPIC + "/"
                    #     + client.get_name() + "/"
                    #     + pmp_definitions.MQTT_AWS_UPDATE_TOPIC + "/"
                    #     #+ pmp_definitions.MQTT_AWS_ACCEPTED_TOPIC, 
                    #     #+ pmp_definitions.MQTT_AWS_DOCUMENTS_TOPIC,
                    #     + pmp_definitions.MQTT_AWS_DELTA_TOPIC,
                    #     pmp_definitions.MQTT_QOS_1,
                    #     self.on_shadow_update_delta_callback)
                
                # Subscribing to user defined topics.
                for client in clients:
                    client.subscribe(
                        pmp_definitions.MQTT_HDR_TOPIC + "/"
                        + client.get_name() + "/"
                        + pmp_definitions.MQTT_PRT_TOPIC + "/"
                        + pmp_definitions.MQTT_EVT_TOPIC + "/"
                        + pmp_definitions.MQTT_THR_TOPIC,
                        pmp_definitions.MQTT_QOS_1,
                        self.on_events_threshold_callback)

                # Edge Computing Initialized.
                print('\nEdge Computing setup complete.\n')
            else:
                for device in self.configuration["setup"]["devices"]:
                    device_name = device["name"]
                    clients.append(device_name)


            # GETTING DATA AND PUBLISHING.

            if self.configuration["setup"]["use_threads_for_polling_sensors"]:
                # Sensors' flags.
                self.env_flags = [False] * len(devices)
                self.ine_tdm_flags = [False] * len(devices)
                self.ine_fdm_flags = [False] * len(devices)

                # Shadow devices' flags.
                shadow_flags = [False] * len(devices)

                # Starting threads.
                for i in range(0, len(devices)):
                    FlagThread(self.set_env_flag, i, ENV_DATA_TIMEOUT_s).start()
                    FlagThread(self.set_tdm_flag, i, INE_TDM_DATA_TIMEOUT_s).start()
                    FlagThread(self.set_fdm_flag, i, INE_FDM_DATA_TIMEOUT_s).start()
                    #if self.configuration["setup"]["use_cloud"]:
                    #    FlagThread(set_shadow_flag, i, SHADOW_GET_TIMEOUT_s).start()

                # Measurements.
                self.initialize_dumping(devices)

                # Demo running.
                print('\nDemo running...\n')
                a = 0
                # Infinite loop.
                while True:
                    for i in range(0, len(devices)):
                        if self.env_flags[i]:
                            # Getting data.
                            data = self.get_env(devices[i])

                            # Publishing data.
                            self.publish_env(data, clients[i])

                            # Resetting flag.
                            self.env_flags[i] = False

                        elif self.ine_tdm_flags[i]:
                            # Getting data.
                            data = self.get_tdm(devices[i])

                            # Publishing data.
                            self.publish_ine_tdm(data, clients[i])

                            # Resetting flag.
                            self.ine_tdm_flags[i] = False

                        elif self.ine_fdm_flags[i]:
                            # Getting data.
                            data = self.get_fdm(devices[i])

                            # Publishing data.
                            self.publish_ine_fdm(data, clients[i])

                            # Resetting flag.
                            self.ine_fdm_flags[i] = False

                        # elif shadow_flags[i] and self.configuration["setup"]["use_cloud"]:
                        #     # Getting shadow's state.
                        #     clients[i].get_shadow_state(self.on_shadow_get_callback, SHADOW_CALLBACK_TIMEOUT_s)

                        #     # Resetting flag.
                        #     shadow_flags[i] = False

            else:
                # Measurements.
                self.initialize_dumping(devices)

                # Demo running.
                print('\nDemo running...\n')

                # Infinite loop.
                while True:
                    for i in range(0, len(devices)):
                        # Getting data.
                        data = self.get_env(devices[i])

                        # Publishing data.
                        self.publish_env(data, clients[i])

                        # Getting data.
                        data = self.get_tdm(devices[i])

                        # Publishing data.
                        self.publish_ine_tdm(data, clients[i])

                        # Getting data.
                        data = self.get_fdm(devices[i])

                        # Publishing data.
                        self.publish_ine_fdm(data, clients[i])

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

    #
    # Printing presentation message.
    #
    def print_intro(self):
        print('\n' + INTRO + '\n')

    #
    # Reading input.
    #
    def read_input(self, argv):
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
    def read_configuration(self, json_configuration_file):
        with open(json_configuration_file, 'r') as fp:
            self.configuration = json.load(fp)
        error = ''
        if self.configuration["setup"]["use_cloud"]:
            self.endpoint = \
                json.load(open(pmp_definitions.GREENGRASS_CONFIG_PATH)
                    )["coreThing"]["iotHost"]
            self.root_ca_path = \
                json.load(open(pmp_definitions.GREENGRASS_CONFIG_PATH)
                    )["crypto"]["caPath"].split('file://')[1]
            if not self.endpoint:
                error += 'Missing endpoint in configuration file.\n'
            if not self.root_ca_path:
                error += 'Missing Root Certification Authority certificate in ' \
                    'configuration file.\n'
        if error is not '':
            print('%sExiting...\n' % (error))
            sys.exit(2)

    #
    # Configure logging.
    #
    def configure_logging(self):
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
    def set_env_flag(self, flag):
        # Setting the flag for getting environmental data.
        self.env_flags[flag] = True

    #
    # Setting the flag for getting time domain data.
    #
    def set_tdm_flag(self, flag):
        # Setting the flag for getting time domain data.
        self.ine_tdm_flags[flag] = True

    #
    # Setting the flag for getting frequency domain data.
    #
    def set_fdm_flag(self, flag):
        # Setting the flag for getting frequency domain data.
        self.ine_fdm_flags[flag] = True

    #
    # Setting the flag for getting shadow state from AWS IoT.
    #
    def set_shadow_flag(self, flag):
        # Setting the flag for getting shadow state from AWS IoT.
        self.shadow_flags[flag] = True

    #
    # Getting handshake data.
    #
    def get_handshake(self, device):
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
    def get_env(self, device):
        if isinstance(device, IOLinkDevice):
            return device.get_env()
        else:
            return [round(1100.0 * random.random(), 3),
                round(100.0 * random.random(), 3),
                round(50.0 * random.random(), 3)]

    #
    # Getting time domain data.
    #
    def get_tdm(self, device):
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
    def get_fdm(self, device):
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
    def publish_handshake(self, data, client):
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
            (client.get_name(), self.timestamp(), state_json_str))
        client.update_shadow_state(
            state_json_str,
            self.on_shadow_update_callback,
            SHADOW_CALLBACK_TIMEOUT_s)

    #
    # Publishing Environmental data.
    #
    def publish_env(self, data, client):
        # Getting a JSON representation of the message to publish.
        data_json = {
            "Pressure": data[EnvIndex.PRESSURE.value], 
            "Humidity": data[EnvIndex.HUMIDITY.value], 
            "Temperature": data[EnvIndex.TEMPERATURE.value]
        }

        # Publishing the message.
        client_name = client.get_name() if isinstance(client, AWSClient) \
            else client
        data_json_str = json.dumps(data_json, sort_keys=True)
        print('[%s] (%s): %s' % \
            (client_name, self.timestamp(), data_json_str))
        if isinstance(client, AWSClient):
            client.publish(
                pmp_definitions.MQTT_HDR_TOPIC + "/" \
                + client_name + "/" \
                + pmp_definitions.MQTT_SNS_TOPIC + "/" \
                + pmp_definitions.MQTT_ENV_TOPIC,
                data_json_str,
                pmp_definitions.MQTT_QOS_0)
        self.dump_env(client_name, data_json_str)

    #
    # Publishing Inertial Time Domain data.
    #
    def publish_ine_tdm(self, data, client):
        # Getting a JSON representation of the message to publish.
        data_json = {
            "RMS_Speed": data[TdmIndex.RMS.value],
            "Peak_Acceleration": data[TdmIndex.PEAK.value]
        }

        # Publishing the message.
        client_name = client.get_name() if isinstance(client, AWSClient) \
            else client
        data_json_str = json.dumps(data_json, sort_keys=True)
        print('[%s] (%s): %s' % \
            (client_name, self.timestamp(), data_json_str))
        if isinstance(client, AWSClient):
            client.publish(
                pmp_definitions.MQTT_HDR_TOPIC + "/" \
                + client_name + "/" \
                + pmp_definitions.MQTT_SNS_TOPIC + "/" \
                + pmp_definitions.MQTT_INE_TOPIC \
                + pmp_definitions.MQTT_TDM_TOPIC,
                data_json_str,
                pmp_definitions.MQTT_QOS_0)
        self.dump_ine_tdm(client_name, data_json_str)

    #
    # Publishing Inertial Frequency Domain data.
    #
    def publish_ine_fdm(self, data, client):
        # Getting a JSON representation of the message to publish.
        data_json = {
            "Ine_FFT": data
        }

        # Publishing the message.
        data_json_tmp = {
            "Ine_FFT": "[" + str(len(data)) + "]"
        }
        client_name = client.get_name() if isinstance(client, AWSClient) \
            else client
        data_json_tmp_str = json.dumps(data_json_tmp, sort_keys=True)
        print('[%s] (%s): %s' % \
            (client_name, self.timestamp(), data_json_tmp_str))
        data_json_str = json.dumps(data_json, sort_keys=True)
        if isinstance(client, AWSClient):
            client.publish(
                pmp_definitions.MQTT_HDR_TOPIC + "/" \
                + client_name + "/" \
                + pmp_definitions.MQTT_SNS_TOPIC + "/" \
                + pmp_definitions.MQTT_INE_TOPIC \
                + pmp_definitions.MQTT_FDM_TOPIC,
                data_json_str,
                pmp_definitions.MQTT_QOS_0)
        self.dump_ine_fdm(client_name, data_json_str)

    #
    # Initializing dumping process.
    #
    def initialize_dumping(self, devices):
        self.env_samples = {}
        self.tdm_samples = {}
        self.fdm_samples = {}
        for device in devices:
            device_name = device.get_name() if isinstance(device, IOLinkDevice) \
                else device
            self.env_samples[device_name] = self.configuration["dump"]["env_samples"]
            self.tdm_samples[device_name] = self.configuration["dump"]["tdm_samples"]
            self.fdm_samples[device_name] = self.configuration["dump"]["fdm_samples"]

    #
    # Dumping Inertial Frequency Domain data.
    #
    def dump_env(self, device_name, data_json_str):
        if self.env_samples[device_name]:
            data_json_str = data_json_str.replace('}', '}\r\n')
            fn = device_name + '_' + pmp_definitions.MQTT_ENV_TOPIC + DUMP_EXT
            fd = open(fn, 'a')
            fd.write(data_json_str)
            fd.close()
            self.env_samples[device_name] -= 1
            self.check_dumping()

    #
    # Dumping Inertial Frequency Domain data.
    #
    def dump_ine_tdm(self, device_name, data_json_str):
        if self.tdm_samples[device_name]:
            data_json_str = data_json_str.replace('}', '}\r\n')
            fn = device_name + '_' + pmp_definitions.MQTT_INE_TOPIC + pmp_definitions.MQTT_TDM_TOPIC + DUMP_EXT
            fd = open(fn, 'a')
            fd.write(data_json_str)
            fd.close()
            self.tdm_samples[device_name] -= 1
            self.check_dumping()

    #
    # Dumping Inertial Frequency Domain data.
    #
    def dump_ine_fdm(self, device_name, data_json_str):
        if self.fdm_samples[device_name]:
            data_json_str = data_json_str.replace(': [[', ': [\r\n[')
            data_json_str = data_json_str.replace('], [', '], \r\n[')
            data_json_str = data_json_str.replace(']]}', ']\r\n]}\r\n')
            fn = device_name + '_' + pmp_definitions.MQTT_INE_TOPIC + pmp_definitions.MQTT_FDM_TOPIC + DUMP_EXT
            fd = open(fn, 'a')
            fd.write(data_json_str)
            fd.close()
            self.fdm_samples[device_name] -= 1
            self.check_dumping()

    #
    # Checking dumping process.
    #
    def check_dumping(self):
        end = 0
        for device_name in self.fdm_samples:
            end += self.env_samples[device_name] + \
                self.tdm_samples[device_name] + \
                self.fdm_samples[device_name]
        if not end:
            print('\nDumping samples completed. Exiting...\n')
            sys.exit(0)

    #
    # Custom shadow callback for "get()" operations.
    #
    def on_shadow_get_callback(self, payload, response_status, token):
        # "payload" is a JSON string ready to be parsed using "json.loads()"
        # both in both Python 2.x and Python 3.x
        print("Get request with token \"" + token + "\" " + response_status)
        #if response_status == "accepted":
        #state_json_str = json.loads(payload)
        #print(state_json_str)

    #
    # Custom shadow callback for "update()" operations.
    #
    def on_shadow_update_callback(self, payload, response_status, token):
        # "payload" is a JSON string ready to be parsed using "json.loads()"
        # both in both Python 2.x and Python 3.x
        print("Update request with token \"" + token + "\" " + response_status)
        #if response_status == "accepted":
        #state_json_str = json.loads(payload)
        #print(state_json_str)

    #
    # Custom shadow callback for "update-delta()" operations.
    #
    # def on_shadow_update_delta_callback(payload, response_status, token):
    #     # "payload" is a JSON string ready to be parsed using "json.loads()"
    #     # both in Python 2.x and Python 3.x
    #     print("Update-Delta request with token \"" + token + "\" " + response_status)
    #     #if response_status == "accepted":
    #     state_json_str = json.loads(payload)
    #     print(state_json_str)

    #
    # Custom shadow callback for "delete()" operations.
    #
    def on_shadow_delete_callback(self, payload, response_status, token):
        # "payload" is a JSON string ready to be parsed using "json.loads()"
        # both in both Python 2.x and Python 3.x
        print("Delete request with token \"" + token + "\" " + response_status)
        #if response_status == "accepted":
        #    state_json_str = json.loads(payload)

    #
    # Custom callback for events.
    #
    def on_events_threshold_callback(self, client, userdata, message):
        client = message.topic.split(pmp_definitions.MQTT_HDR_TOPIC + '/')[1]
        client = client[:client.find('/')]
        message_json = json.loads(message.payload.decode('utf-8'))
        message_json["client"] = client
        severity = message_json["severity"]
        print('[%s] (%s): Event of severity \"%d\": %s%s' % (\
            client,
            self.timestamp(),
            severity,
            message_json["msg"],
            '' if not severity else (' (%s)' % (message_json["info"]["value"]))))

    #
    # Get the current timestamp.
    #
    def timestamp(self):
        #return datetime.now().time()
        return time.strftime("%H:%M:%S")


# RUNNING MAIN APPLICATION

if __name__ == "__main__":
    try:
        pmp = PMP(sys.argv[1:])
        pmp.start()
    except Exception as e:
        print(e)
