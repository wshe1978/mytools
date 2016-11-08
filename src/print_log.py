#!/usr/local/bin/python3

import argparse
import json

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file-name', action='store', dest='file_name', required=True, help='specify name of log file')
    args = parser.parse_args()

    with open(args.file_name) as f:
        logs = [line for line in f.read().split('\n') if line]
        logs = [json.loads(line) for line in logs]
        for i in range(len(logs)):
            log = logs[i]['log'].replace('\n', '')
            print(log)
