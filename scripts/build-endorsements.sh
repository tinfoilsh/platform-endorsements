#!/bin/bash
# Assemble platform-endorsements.json from the measured platform data
# (hardware-measurements.json, produced by scripts/measure.sh) plus the
# reviewed machines.json and policies.json inputs.
# Run from the repository root: ./scripts/build-endorsements.sh
set -e

python3 scripts/validate.py

jq -n \
  --slurpfile measurements hardware-measurements.json \
  --slurpfile machines machines.json \
  --slurpfile policies policies.json \
  '{
    format: "https://tinfoil.sh/predicate/platform-endorsements/v1",
    measurements: $measurements[0],
    machines: $machines[0],
    policies: $policies[0]
  }' > platform-endorsements.json

echo "platform-endorsements.json assembled:"
jq '{measurements: (.measurements | length), machines: (.machines | length), policies: (.policies | length)}' platform-endorsements.json
