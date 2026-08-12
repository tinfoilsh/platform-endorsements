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
- `platform.json` — reviewed CPU, memory, disk, QEMU, and PCI topology inputs
  used to reconstruct every supported platform offline
- `toolchain.lock.json` — pinned `tdx-measure` and OVMF inputs, including
  download URLs and SHA-256 digests
- `boot/` — shared OVMF boot variables
- `platforms/` — each slug's reviewed `shape.json` (`cpus`, `memory_mb`,
  `disks`, optional `gpus`), merged into every published measurement entry
- `measure.py` — fetches the pinned toolchain, reconstructs ACPI tables, and
  generates `hardware-measurements.json`
- `scripts/` — tooling (run from the repository root):
  - `validate.py` — validate machines, policies, platform inputs, and shapes
    (runs in CI on every PR and release)
  - `build-endorsements.sh` — assemble `platform-endorsements.json`

## Data provenance

- `machines.json` is generated from Tinfoil's machine inventory: hardware
  identifiers are extracted from each production machine (AMD `CHIP_ID` via
  the SEV firmware; Intel PPID from the platform's PCK certificate) and
  mapped to a policy. Entries are reviewed via pull request; one identifier
  maps to exactly one policy by construction.
- `policies.json` is hand-authored and review-gated: its values define what
  Tinfoil clients enforce when verifying attestation from these machines.
- TDX ACPI tables are reconstructed during every build from the reviewed
  `platform.json` inputs. They are not copied from a running CVM or stored in
  the repository. All supported platforms use QEMU 10.1.0.

## Updating

- **Add or replace a machine**: add/change one line in `machines.json`
  (identifier -> policy name), open a PR. CI validates formats and policy
  references.
- **Remove a machine**: machines that leave the fleet (decommissioned,
  lease returned, CPU replaced) MUST be removed from `machines.json`.
- **Change a policy**: edit `policies.json`, open a PR. All machines
  referencing the policy move atomically with the release.
- **Add a platform configuration**: add its production inputs to
  `platform.json`, add `platforms/<name>/shape.json`, reference the slug from
  a TDX policy, then regenerate the endorsements artifact. CI requires the
  configured CPU, memory, and disk values to match the reviewed shape.

## Usage

Generate measurements and the endorsements artifact:

   ```bash
   ./measure.py
   ./scripts/build-endorsements.sh
   ```

Pass one or more platform slugs to `measure.py` to generate a subset, or use
`--output` to select another output path.

## Measurement generation

`measure.py` downloads and verifies the pinned `tdx-measure` and OVMF inputs,
translates each `platform.json` entry into the ordered QEMU 10.1.0 device
topology used in production, reconstructs the ACPI tables in a temporary
directory, and computes the final TDX measurements. Generated tables and
intermediate metadata are intentionally not committed.

Device stand-ins reproduce the measured PCI topology without requiring real
hardware: backend-free virtio devices occupy the fixed v0.11 guest slots,
`pci-testdev` occupies GPU endpoints, sparse memory backs large guest shapes,
and GPU root ports preserve the reviewed PCI aperture.

## GitHub Actions

On each tag push, the release workflow:
1. Validates `machines.json` and `policies.json`
2. Downloads and checksum-verifies the pinned toolchain
3. Reconstructs ACPI, generates measurements, and assembles
   `platform-endorsements.json`
4. Creates a Sigstore attestation for the artifact (predicate
   `https://tinfoil.sh/predicate/platform-endorsements/v1`)
5. Publishes the artifact and its hash file as release assets
6. Notifies the legacy repository to republish the v1 measurements artifact

The attestation is published to Sigstore's transparency log, ensuring the
integrity and provenance of the measurements and endorsements.
