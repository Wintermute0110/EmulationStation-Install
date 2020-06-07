#!/bin/sh

esdir="$(dirname $0)"
echo "Starting emulationstation.sh in $esdir"
while true; do
    rm -f /tmp/es-restart /tmp/es-sysrestart /tmp/es-shutdown
    "$esdir/emulationstation" "$@"
    ret=$?
    echo "EmulationStation returned $ret"
    if [ -f /tmp/es-restart ]; then
        echo "Restarting EmulationStation..."
        continue
    fi
    if [ -f /tmp/es-sysrestart ]; then
	echo "Rebooting system..."
        rm -f /tmp/es-sysrestart
        # reboot
        break
    fi
    if [ -f /tmp/es-shutdown ]; then
	echo "Shutting down system..."
        rm -f /tmp/es-shutdown
        # poweroff
        break
    fi
    break
done
echo "Ending emulationstation.sh. Will return $ret"
exit $ret
