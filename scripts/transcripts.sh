#!/bin/bash

set -ex

mkdir -p transcripts/

for dir in platforms/*; do
    name=$(basename $dir)
    echo "Generating transcript for $name"
    ./tdx-measure $dir/metadata.json --platform-only --transcript transcripts/${name}.txt
done