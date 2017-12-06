#!/usr/bin/env bash

fail () {
    echo "Sorry, startup scripts only work on Debian and derivatives."
    exit 1
}

PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

. /lib/init/vars.sh
. /lib/lsb/init-functions

[ "$(type -t log_daemon_msg)" = "function" ] || fail
[ "$(type -t log_end_msg)" = "function" ] || fail
[ "$(type -t status_of_proc)" = "function" ] || fail
[ "$(type -t start-stop-daemon)" = "file" ] || fail
