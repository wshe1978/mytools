#!/usr/bin/env bash

for i in $( ls /Users/weiapplatix/Documents/Work/projects/experiments/experiment_fetch ); do
    python3 /Users/weiapplatix/Documents/Work/projects/mytools/src/cache_performance.py write_cache --repo $i
done

for i in $( ls /Users/weiapplatix/Documents/Work/projects/experiments/experiment_fetch ); do
    python3 /Users/weiapplatix/Documents/Work/projects/mytools/src/cache_performance.py read_cache --repo $i
done