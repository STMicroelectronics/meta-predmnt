#!/bin/sh

ps aux | grep main_pmp_gui | awk '{print $2}' | xargs kill -9
/greengrass/ggc/core/greengrassd stop

