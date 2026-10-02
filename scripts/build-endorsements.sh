#!/bin/bash
# Assemble platform-endorsements.json from the measured platform data
# (hardware-measurements.json, produced by measure.py) plus the
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

jq '
  .measurements = {} |
  .policies |= with_entries(
    if .value.platform == "sev-snp" then
      .value.sev_snp |= (del(.host_data) + {config_binding: "sha256"})
    elif .value.platform == "tdx" then
      .value.tdx |= (del(.platform_measurements) + {config_binding: "sha256"})
    else error("unsupported IGVM platform")
    end
  )
' platform-endorsements.json > platform-endorsements-igvm.json
