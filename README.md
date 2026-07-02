# Tinfoil Hardware Measurements

This repository contains the platform configurations and machine endorsements
trusted by Tinfoil clients when verifying remote attestation reports. It
publishes two Sigstore-attested artifacts per release:

- `platform-endorsements.json` — the platform measurements plus the endorsed
  machine identities (`machines.json`) and their validation policies
  (`policies.json`)
- `hardware-measurements.json` (legacy) — TDX platform measurements
  (`MRTD`/`RTMR0`) per platform configuration, kept for existing verifiers

## Structure

- `machines.json` — endorsed machine identities: a flat map of hardware
  identifier to policy name. AMD SEV-SNP machines are keyed by their 64-byte
  `CHIP_ID` (128 hex chars; Turin hardware IDs are 8 bytes zero-padded to 64),
  Intel TDX machines by their 16-byte PPID (32 hex chars)
- `policies.json` — named validation policies. Each policy declares its
  `platform` (`sev-snp` or `tdx`) and the platform-specific verification
  parameters (TCB floors, guest policy, accepted MR_SEAM values, allowed
  platform measurements, ...)
- `platforms/` — platform-specific boot configurations and metadata used to
  compute TDX measurements
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
- **Change a policy**: edit `policies.json`, open a PR. All machines
  referencing the policy move atomically with the release.
- **Add a platform configuration**: add `platforms/<name>/` with
  `metadata.json` and metadata blobs, then re-measure.

## Usage

1. Fetch required tools:
   ```bash
   ./scripts/fetch-tdx-measure.sh
   ./scripts/fetch-ovmf.sh
   ```

2. Generate measurements and the v2 artifact:
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
3. Generates hardware measurements for all platforms and assembles the v2
   artifact
4. Creates Sigstore attestations for both `hardware-measurements.json`
   (predicate `https://tinfoil.sh/predicate/hardware-measurements/v1`) and
   `platform-endorsements.json` (predicate
   `https://tinfoil.sh/predicate/platform-endorsements/v1`)
5. Publishes all artifacts and hash files as release assets

Both attestations are published to Sigstore's transparency log, ensuring the
integrity and provenance of the measurements and endorsements. Every release
includes the v1 assets for compatibility with existing verifiers.
