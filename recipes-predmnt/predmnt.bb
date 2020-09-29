# Copyright (C) 2019, STMicroelectronics - All Rights Reserved

SUMMARY = "Recipe to install Predictive Maintenance Application"

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
LIC_FILES_CHKSUM = "file://../LICENSE.txt;md5=b9d23a528e48fc31686903288ed5df59"

# No information for SRC_URI yet (only an external source tree was specified)
# file://startup
SRC_URI = " \
    file://pmp.py \
    file://pmp_definitions.py \
    file://start_pmp.sh \
    file://stop_pmp.sh \
    file://gui \
    file://media \
    file://utils \
    file://start_up_predmnt_launcher.sh \
    file://LICENSE.txt \
    "

do_configure[noexec] = "1"
do_compile[noexec] = "1"

do_install () {
    # Application.
    install -d ${D}${prefix}/local/predmnt
    install -d ${D}${prefix}/local/predmnt/gui
    install -d ${D}${prefix}/local/predmnt/media
    install -d ${D}${prefix}/local/predmnt/utils
    install -m 0666 ${WORKDIR}/pmp.py ${D}${prefix}/local/predmnt/
    install -m 0666 ${WORKDIR}/pmp_definitions.py ${D}${prefix}/local/predmnt/
    install -m 0755 ${WORKDIR}/start_pmp.sh ${D}${prefix}/local/predmnt/
    install -m 0755 ${WORKDIR}/stop_pmp.sh ${D}${prefix}/local/predmnt/
    install -m 0666 ${WORKDIR}/gui/* ${D}${prefix}/local/predmnt/gui/
    install -m 0666 ${WORKDIR}/media/* ${D}${prefix}/local/predmnt/media/
    install -m 0666 ${WORKDIR}/utils/* ${D}${prefix}/local/predmnt/utils/
    install -m 0444 ${WORKDIR}/LICENSE.txt ${D}${prefix}/local/predmnt/

    # Startup.
    install -d ${D}${prefix}/local/weston-start-at-startup/
    install -m 0755 ${WORKDIR}/start_up_predmnt_launcher.sh ${D}${prefix}/local/weston-start-at-startup/
}

FILES_${PN} += " ${prefix}/local/predmnt/"
FILES_${PN} += " ${prefix}/local/weston-start-at-startup/"
