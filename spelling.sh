#!/bin/bash

SPELLING="$(cat README.md | aspell -a | sed -n '/&/p')"

if [[ $SPELLING == "" ]]; then
    exit 0
else
    echo "Found spelling mistakes!"
    echo $SPELLING
    exit 1
fi
