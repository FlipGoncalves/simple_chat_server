#!/bin/bash

clients=("foo" "bar")

# run processes and store pids in array
for i in ${!clients[@]}; do
    sh tests/fast${i}.sh | python3 ${clients[$i]}.py > /dev/null &
    pids[${i}]=$!
done

# wait for all pids
for i in "${!pids[@]}"; do
    if wait ${pids[$i]}; then
        echo "fast$i.sh PASSED"
    else
        echo "fast$i.sh FAILED"
        exit 1
    fi
done

diff -u foo.py.log bar.py.log
