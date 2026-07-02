#!/bin/bash

set -ex

rm -rf measurements/
mkdir -p measurements/

for dir in platforms/*; do
    name=$(basename $dir)
    echo "Measuring $name"
    ./tdx-measure $dir/metadata.json --platform-only --json-file measurements/${name}.json
done

# Combine all measurement files into one JSON, with platform names as keys
for file in measurements/*.json; do
    name=$(basename $file | cut -d. -f1)
    # Create a JSON with the platform name as the key
    jq --arg name "$name" '. as $data | {($name): $data}' "$file" > "$file.tmp"
    mv "$file.tmp" "$file"
done

# # Merge all platform JSONs into a single file
jq -s 'reduce .[] as $item ({}; . * $item)' measurements/*.json > hardware-measurements.json

rm -rf measurements/
