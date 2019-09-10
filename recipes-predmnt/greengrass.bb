# Copyright (C) 2019, STMicroelectronics - All Rights Reserved

SUMMARY = "Recipe to install Amazon AWS Greengrass"

# Recipe created by recipetool
# This is the basis of a recipe and may need further editing in order to be fully functional.
# (Feel free to remove these comments when editing.)

# Unable to find any files that looked like license statements. Check the accompanying
# documentation and source headers and set LICENSE and LIC_FILES_CHKSUM accordingly.
#
# NOTE: LICENSE is being set to "CLOSED" to allow you to at least start building - if
# this is not accurate with respect to the licensing of the software being built (it
# will not be in most cases) you must specify the correct value before using this
# recipe for anything other than initial testing/development!
LICENSE = "CLOSED"
LIC_FILES_CHKSUM = ""

# No information for SRC_URI yet (only an external source tree was specified)
SRC_URI = "https://d1onfpft10uf5o.cloudfront.net/greengrass-core/downloads/1.9.2/greengrass-linux-armv7l-1.9.2.tar.gz"
SRC_URI[md5sum] = "63a1f6aae22260be19f34f278f7e7833"
SRC_URI[sha256sum] = "4bc0bc8a938cdb3d846df92e502155c6ec8cbaf1b63dfa9f3cc3a51372d95af5"

do_configure[noexec] = "1"
do_compile[noexec] = "1"

do_install () {
    mv ${WORKDIR}/greengrass ${D}/greengrass
}

FILES_${PN} += "/greengrass"

INSANE_SKIP_${PN} += "This may be due to host contamination"