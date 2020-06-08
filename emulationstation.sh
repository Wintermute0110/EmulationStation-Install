#!/bin/sh

# * A link named emulationstation pointing to the ES executable must be in the
#   same directory as this script file.
# * reboot and poweroff are symlinks to systemctl. systemd only allows to
#   shutdown the system to logged in users. This is the reason those
#   commands cannot be used in this script. DBus must be used
#   for rebooting/powering off.

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
        dbus-send --system --print-reply --dest=org.freedesktop.login1 /org/freedesktop/login1 "org.freedesktop.login1.Manager.Reboot" boolean:true
        break
    fi
    if [ -f /tmp/es-shutdown ]; then
	echo "Shutting down system..."
        rm -f /tmp/es-shutdown
        # poweroff
        dbus-send --system --print-reply --dest=org.freedesktop.login1 /org/freedesktop/login1 "org.freedesktop.login1.Manager.PowerOff" boolean:true
        break
    fi
    break
done
echo "Ending emulationstation.sh. Will return $ret"
exit $ret
