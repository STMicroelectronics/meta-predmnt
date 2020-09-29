#!/bin/sh

ps aux | grep *pmp*.py | awk '{print $2}' | xargs kill -9
/greengrass/ggc/core/greengrassd stop
