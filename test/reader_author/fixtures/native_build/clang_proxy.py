#!/usr/bin/python3
"""Record actual argv, then exercise real Clang, including a bad IR control."""
import json
import os
import sys
with open(os.environ['NATIVE_TOOL_LOG'], 'a') as log:
    log.write(json.dumps(sys.argv[1:]) + '\n')
args = sys.argv[1:]
if os.environ.get('NATIVE_BAD_IR') and '-c' in args:
    args[args.index('-c') + 1] = os.environ['NATIVE_BAD_IR']
os.execv(os.environ['NATIVE_REAL_CLANG'], [os.environ['NATIVE_REAL_CLANG'], *args])
