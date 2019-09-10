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
LICENSE = "CLOSED"
LIC_FILES_CHKSUM = ""

# No information for SRC_URI yet (only an external source tree was specified)
# file://startup
SRC_URI = " \
    file://pmp.py \
    file://pmp.cfg \
    file://setup_gw.py \
    file://setup_pmp.py \
    file://start_pmp.sh \
    file://stop_pmp.sh \
    "

do_configure[noexec] = "1"
do_compile[noexec] = "1"

do_install () {
    install -d ${D}${prefix}/local/predmnt
    install -m 0666 ${WORKDIR}/pmp.py ${D}${prefix}/local/predmnt/
    install -m 0666 ${WORKDIR}/pmp.cfg ${D}${prefix}/local/predmnt/
    install -m 0666 ${WORKDIR}/setup_gw.py ${D}${prefix}/local/predmnt/
    install -m 0666 ${WORKDIR}/setup_pmp.py ${D}${prefix}/local/predmnt/
    install -m 0755 ${WORKDIR}/start_pmp.sh ${D}${prefix}/local/predmnt/
    install -m 0755 ${WORKDIR}/stop_pmp.sh ${D}${prefix}/local/predmnt/

#    install -d ${D}${prefix}/local/weston-start-at-startup/
#    install -m 0755 ${WORKDIR}/startup/start_up_terminal.sh ${D}${prefix}/local/weston-start-at-startup/
}

FILES_${PN} += " ${prefix}/local/predmnt/"
#FILES_${PN} += " ${prefix}/local/weston-start-at-startup/"
