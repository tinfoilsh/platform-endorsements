#!/bin/bash

set -ex

rm -rf measurements/
mkdir -p measurements/

for dir in platforms/*; do
    name=$(basename $dir)
    echo "Measuring $name"
    ./tdx-measure $dir/metadata.json --platform-only --json-file measurements/${name}.json
done

# Combine all measurement files into one JSON, with platform names as keys,
# merging in the slug's reviewed shape descriptor. shape is required on
# every measurement (v3 parsers reject entries without it).
for file in measurements/*.json; do
    name=$(basename $file | cut -d. -f1)
    if [ ! -f "platforms/${name}/shape.json" ]; then
        echo "platforms/${name}/shape.json missing" >&2
        exit 1
    fi
    jq --arg name "$name" --slurpfile shape "platforms/${name}/shape.json" \
        '{($name): (. + {shape: $shape[0]})}' "$file" > "$file.tmp"
    mv "$file.tmp" "$file"
done

# # Merge all platform JSONs into a single file
jq -s 'reduce .[] as $item ({}; . * $item)' measurements/*.json > hardware-measurements.json

rm -rf measurements/
