#!/usr/bin/env bash

for i in `seq 1 5 100`; do
    for j in `seq 1 5`; do
        python3 src/time_performance.py concurrent_search_commits --concurrency $i --repo subversion
    done
done