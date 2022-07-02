#!/bin/bash

clients=("foo" "bar")

# run processes and store pids in array
for i in ${!clients[@]}; do
    sh tests/extra${i}.sh | python3 ${clients[$i]}.py > /dev/null &
    pids[${i}]=$!
done

# wait for all pids
for i in "${!pids[@]}"; do
    if wait ${pids[$i]}; then
        echo "extra$i.sh PASSED"
    else
        echo "extra$i.sh FAILED"
        exit 1
    fi
done

# Bar is not in channel #cd so it missed 2 messages from Foo, we append those messages and both should have the same log
tail -n 2 foo.py.log >> bar.py.log
diff -u foo.py.log bar.py.log

