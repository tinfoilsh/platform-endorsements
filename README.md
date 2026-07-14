# Tinfoil Platform Endorsements

This repository is the source of truth for the platform configurations and
machine endorsements trusted by Tinfoil clients when verifying remote
attestation reports. Each release publishes a Sigstore-attested artifact:

- `platform-endorsements.json` — TDX platform measurements, the endorsed
  machine identities (`machines.json`), and their validation policies
  (`policies.json`)

Predicate: `https://tinfoil.sh/predicate/platform-endorsements/v1`

Legacy note: the [`hardware-measurements`](https://github.com/tinfoilsh/hardware-measurements)
repository republishes the `measurements` section of each release as the
legacy `hardware-measurements.json` artifact under its own signing identity,
for verifiers that predate this repository. It is on a deprecation path and
will be archived when legacy client support ends.

## Structure

- `machines.json` — endorsed machine identities: a flat map of hardware
  identifier to policy name. AMD SEV-SNP machines are keyed by their 64-byte
  `CHIP_ID` (128 hex chars; Turin hardware IDs are 8 bytes zero-padded to 64),
  Intel TDX machines by their 16-byte PPID (32 hex chars)
- `policies.json` — named validation policies. Each policy declares its
  `platform` (`sev-snp` or `tdx`) and the platform-specific verification
  parameters (TCB floors, guest policy, the expected MR_SEAM, allowed
  platform measurements, ...). Every policy member is required — verifiers
  parse fail-closed, rejecting unknown or absent members
- `platforms/` — platform-specific boot configurations and metadata used to
  compute TDX measurements, plus each slug's `shape.json` (the VM shape the
  measurement is valid for: `cpus`, `memory_mb`, `disks`, optional `gpus`),
  merged into every published measurement entry
- `scripts/` — tooling (run from the repository root):
  - `measure.sh` — generate measurements for all platforms
  - `fetch-tdx-measure.sh` / `fetch-ovmf.sh` — download build inputs
  - `validate.py` — validate `machines.json` + `policies.json` (runs in CI
    on every PR and release)
  - `build-endorsements.sh` — assemble `platform-endorsements.json`
  - `transcripts.sh` — human-readable transcripts of platform metadata
  - `analyze.py` — compare metadata files across platform configs

## Data provenance

- `machines.json` is generated from Tinfoil's machine inventory: hardware
  identifiers are extracted from each production machine (AMD `CHIP_ID` via
  the SEV firmware; Intel PPID from the platform's PCK certificate) and
  mapped to a policy. Entries are reviewed via pull request; one identifier
  maps to exactly one policy by construction.
- `policies.json` is hand-authored and review-gated: its values define what
  Tinfoil clients enforce when verifying attestation from these machines.

## Updating

- **Add or replace a machine**: add/change one line in `machines.json`
  (identifier -> policy name), open a PR. CI validates formats and policy
  references.
- **Remove a machine**: machines that leave the fleet (decommissioned,
  lease returned, CPU replaced) MUST be removed from `machines.json`.
- **Change a policy**: edit `policies.json`, open a PR. All machines
  referencing the policy move atomically with the release.
- **Add a platform configuration**: add `platforms/<name>/` with
  `metadata.json`, metadata blobs, and `shape.json`, then re-measure.

## Usage

1. Fetch required tools:
   ```bash
   ./scripts/fetch-tdx-measure.sh
   ./scripts/fetch-ovmf.sh
   ```

2. Generate measurements and the endorsements artifact:
   ```bash
   ./scripts/measure.sh
   ./scripts/build-endorsements.sh
   ```

## Platforms

Each platform directory contains:
- `metadata.json` - Configuration file with hardware specifications
- `metadata/` - Binary files with platform-specific data

## GitHub Actions

On each tag push, the release workflow:
1. Validates `machines.json` and `policies.json`
2. Downloads the required tools (`tdx-measure` and `OVMF`)
3. Generates hardware measurements for all platforms and assembles
   `platform-endorsements.json`
4. Creates a Sigstore attestation for the artifact (predicate
   `https://tinfoil.sh/predicate/platform-endorsements/v1`)
5. Publishes the artifact and its hash file as release assets
6. Notifies the legacy repository to republish the v1 measurements artifact

The attestation is published to Sigstore's transparency log, ensuring the
integrity and provenance of the measurements and endorsements.
