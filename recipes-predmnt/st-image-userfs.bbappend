# Copyright (C) 2022, STMicroelectronics - All Rights Reserved

SUMMARY = "Recipe to install user packages to userfs partition"

PACKAGE_INSTALL += "\
    ${@bb.utils.contains('DISTRO_FEATURES', 'wayland', 'greengrass', '', d)} \
    ${@bb.utils.contains('DISTRO_FEATURES', 'wayland', 'predmnt', '', d)} \
    "
