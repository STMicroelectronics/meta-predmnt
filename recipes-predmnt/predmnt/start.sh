#!/bin/sh

ps aux | grep main_pmp_gui | awk '{print $2}' | xargs kill -9
export PYTHONPATH=$PYTHONPATH:/usr/local/predmnt/
if [ -z "$1" ]; then
    echo
    echo "Restarting AWS Greengrass Edge Computing service..."
    /greengrass/ggc/core/greengrassd restart && python3 /usr/local/predmnt/pmp.py -c /usr/local/predmnt/pmp.json
elif [ $1 = "--gui" ]; then
    python3 /usr/local/predmnt/gui/main_pmp_gui.py
else
    echo
    echo "Usage:"
    echo
    echo "$0 [--gui]"
    echo
fi

