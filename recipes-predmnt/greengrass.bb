# Copyright (C) 2022, STMicroelectronics - All Rights Reserved

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
LIC_FILES_CHKSUM = "file://../image/greengrass/ota/ota_agent_v1.3.0/LICENSE/THIRD-PARTY-LICENSES;md5=632ff94a8185c978475c184e49112276 \
                    file://../image/greengrass/ota/ota_agent_v1.3.0/LICENSE/LICENSE;md5=cbd8d279038a7a6174c17a9342aadab7 \
                    file://../image/greengrass/ggc/packages/1.11.0/THIRD-PARTY-LICENSES;md5=d3fb176f85edb203d99ed157c1301989 \
                    file://../image/greengrass/ggc/packages/1.11.0/LICENSE;md5=cbd8d279038a7a6174c17a9342aadab7 \
"

# No information for SRC_URI yet (only an external source tree was specified)
SRC_URI = "https://d1onfpft10uf5o.cloudfront.net/greengrass-core/downloads/1.11.0/greengrass-linux-armv7l-1.11.0.tar.gz"
SRC_URI[md5sum] = "c5f2981d724e200c0d68ee41e6f6b47c"
SRC_URI[sha256sum] = "af6ac0b277193a17d59b010071e153aa3d9aca1136062dd044caab3a9b663b13"

do_configure[noexec] = "1"
do_compile[noexec] = "1"

do_install () {
    mv ${WORKDIR}/greengrass ${D}/greengrass
}

FILES_${PN} += "/greengrass"
