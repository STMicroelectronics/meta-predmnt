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
LICENSE = "Proprietary"
LIC_FILES_CHKSUM = "file://../image/greengrass/ota/ota_agent_v1.2.0/LICENSE/THIRD-PARTY-LICENSES;md5=632ff94a8185c978475c184e49112276 \
                    file://../image/greengrass/ota/ota_agent_v1.2.0/LICENSE/LICENSE;md5=cbd8d279038a7a6174c17a9342aadab7 \
                    file://../image/greengrass/ggc/packages/1.10.0/THIRD-PARTY-LICENSES;md5=1f0ad815f019455e3a0efe55e888a69a \
                    file://../image/greengrass/ggc/packages/1.10.0/LICENSE;md5=cbd8d279038a7a6174c17a9342aadab7 \
"

# No information for SRC_URI yet (only an external source tree was specified)
SRC_URI = "https://d1onfpft10uf5o.cloudfront.net/greengrass-core/downloads/1.10.0/greengrass-linux-armv7l-1.10.0.tar.gz"
SRC_URI[md5sum] = "e54bb57929bc278ea89737c4abcd89e8"
SRC_URI[sha256sum] = "91f3d92dca977ea504921c7dbae96a926adce441c8f9ec1896e4c8cf085d6d2e"

do_configure[noexec] = "1"
do_compile[noexec] = "1"

do_install () {
    mv ${WORKDIR}/greengrass ${D}/greengrass
}

FILES_${PN} += "/greengrass"
