#!/usr/bin/env python

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
# This file defines useful constants for the Predictive Maintenance application.


# CONSTANTS

# URIs.
HOME_PATH = '/home/root'
PMP_PATH = '/usr/local/predmnt'
PMP_CONFIGURATION_PATH = PMP_PATH + '/pmp.json'
GREENGRASS_PATH = '/greengrass'
GREENGRASS_CONFIG_PATH = GREENGRASS_PATH + '/config/config.json'
DEVICE_CERTIFICATES_PATH = PMP_PATH + '/devices_pmp_aws'
GATEWAY_RULES_PATH = '/etc/sysctl.d/98-gateway.conf'

# Python packages to install through "pip" tool.
PYTHON_PIP_UPGRADE = 'pip3 install --upgrade pip'
PYTHON_PACKAGES_TO_INSTALL = 'awsiotpythonsdk wire-st-sdk edge-st-sdk'

# Cloud's default MQTT Topics.
MQTT_AWS_HEADER_TOPIC = "$aws/things"
MQTT_AWS_GET_TOPIC = "shadow/get"
MQTT_AWS_UPDATE_TOPIC = "shadow/update"
MQTT_AWS_ACCEPTED_TOPIC = "accepted"
MQTT_AWS_DELTA_TOPIC = "delta"
MQTT_AWS_DOCUMENTS_TOPIC = "documents"

# Custom MQTT Topics for PMP.
MQTT_HDR_TOPIC = "pm"
MQTT_PRT_TOPIC = "v2"
MQTT_CFG_TOPIC = "configuration"
MQTT_SNS_TOPIC = "sense"
MQTT_ENV_TOPIC = "environmental"
MQTT_INE_TOPIC = "inertial"
MQTT_ACO_TOPIC = "acoustic"
MQTT_TDM_TOPIC = "_tdm"
MQTT_FDM_TOPIC = "_fdm"
MQTT_EVT_TOPIC = "events"
MQTT_THR_TOPIC = "threshold"
MQTT_GUI_TOPIC = "gui"

# MQTT QoS.
MQTT_QOS_0 = 0
MQTT_QOS_1 = 1

# Events.
EVENTS = ["normal", "warning", "alert", "critical"]
COLORS = ["#00FF00", "#FFCC00", "#FF0000", "#0000FF"]

# Default PMP configuration.
DEFAULT_PMP_CONFIGURATION_JSON = \
{
    "serial_port": {
        "name": "/dev/ttyUSB0",
        "baudrate_bits_per_second": 230400
    },
    "setup": {
        "use_sensors": True,
        "use_cloud": True,
        "use_threads_for_polling_sensors": True,
        "device_certificates_path": DEVICE_CERTIFICATES_PATH,
        "devices": []
    },
    "dump": {
        "env_samples": 0,
        "tdm_samples": 0,
        "fdm_samples": 0
    }
}
