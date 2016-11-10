#!/usr/bin/env bash

for i in $( ls /Users/weiapplatix/Documents/Work/projects/experiments/experiment_fetch ); do
    python3 /Users/weiapplatix/Documents/Work/projects/mytools/src/space_performance.py search_commits --repo $i
done