#!/usr/bin/env python3
"""CI validation for the platform-endorsements inputs (machines.json + policies.json).

Rules:
  1. every machines.json value names an existing, schema-valid policy
  2. identifier format matches the mapped policy's platform
     (128 lowercase hex chars for sev-snp, 32 for tdx)
  3. no duplicate identifiers (detected at JSON text level)
  4. machines.json carries identifiers and policy names only
  5. every platform_measurements reference resolves to a platforms/ slug
  6. all hex lowercase

Exits non-zero with all violations listed.
"""

import json
import re
import sys
from pathlib import Path

HEX_RE = re.compile(r"^[0-9a-f]+$")

SEV_ID_LEN = 128
PPID_LEN = 32
TURIN_HWID_LEN = 16

SEV_FIELDS = {
    "minimum_build", "minimum_api_version", "minimum_guest_svn",
    "minimum_tcb", "minimum_launch_tcb", "guest_policy", "platform_info",
    "permit_provisional_firmware", "vmpl",
}
SEV_OPTIONAL_FIELDS = {
    "host_data", "image_id", "family_id",
    "require_author_key", "require_id_block",
    "minimum_launch_mitigation_vector", "minimum_current_mitigation_vector",
}
TCB_FIELDS = {"bl_spl", "tee_spl", "snp_spl", "ucode_spl"}
# Turin (family 1Ah) TCBs carry a fifth component; optional for Genoa policies.
TCB_OPTIONAL_FIELDS = {"fmc_spl"}
GUEST_POLICY_FIELDS = {"debug", "smt", "migrate_ma", "single_socket"}
GUEST_POLICY_OPTIONAL_FIELDS = {
    "cxl_allowed", "mem_aes256_xts", "rapl_dis", "ciphertext_hiding_dram",
    "page_swap_disable",
}
PLATFORM_INFO_FIELDS = {
    "smt_enabled", "tsme_enabled", "ecc_enabled", "rapl_disabled",
    "ciphertext_hiding_dram",
}
TDX_FIELDS = {
    "qe_vendor_id", "minimum_qe_svn", "minimum_pce_svn",
    "minimum_tee_tcb_svn", "mr_seam", "td_attributes", "xfam",
    "mr_config_id_zero", "mr_owner_zero", "mr_owner_config_zero",
    "minimum_tcb_evaluation_data_number", "platform_measurements",
}
SHAPE_FIELDS = {"cpus", "memory_mb", "gpus", "disks"}

errors: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def no_duplicates_hook(pairs):
    keys = [k for k, _ in pairs]
    dupes = {k for k in keys if keys.count(k) > 1}
    if dupes:
        err(f"duplicate JSON keys: {sorted(dupes)}")
    return dict(pairs)


def load(path: Path):
    try:
        return json.loads(path.read_text(), object_pairs_hook=no_duplicates_hook)
    except FileNotFoundError:
        err(f"{path}: missing")
    except json.JSONDecodeError as exc:
        err(f"{path}: invalid JSON: {exc}")
    return None


def check_hex(context: str, value, length: int) -> None:
    if not isinstance(value, str) or len(value) != length or not HEX_RE.match(value):
        err(f"{context}: expected {length} lowercase hex chars, got {value!r}")


def validate_sev_policy(name: str, block: dict) -> None:
    unknown = set(block) - SEV_FIELDS - SEV_OPTIONAL_FIELDS
    if unknown:
        err(f"policy {name}: unknown sev_snp fields {sorted(unknown)}")
    for tcb_field in ("minimum_tcb", "minimum_launch_tcb"):
        tcb = block.get(tcb_field, {})
        if not (TCB_FIELDS <= set(tcb) <= TCB_FIELDS | TCB_OPTIONAL_FIELDS):
            err(f"policy {name}: {tcb_field} must have {sorted(TCB_FIELDS)} "
                f"(optionally {sorted(TCB_OPTIONAL_FIELDS)})")
        for k, v in tcb.items():
            if not isinstance(v, int) or not 0 <= v <= 255:
                err(f"policy {name}: {tcb_field}.{k} out of range: {v!r}")
    gp = set(block.get("guest_policy", {}))
    if not (GUEST_POLICY_FIELDS <= gp <= GUEST_POLICY_FIELDS | GUEST_POLICY_OPTIONAL_FIELDS):
        err(f"policy {name}: guest_policy must have {sorted(GUEST_POLICY_FIELDS)} "
            f"(optionally {sorted(GUEST_POLICY_OPTIONAL_FIELDS)})")
    if set(block.get("platform_info", {})) != PLATFORM_INFO_FIELDS:
        err(f"policy {name}: platform_info must have exactly {sorted(PLATFORM_INFO_FIELDS)}")
    if not re.match(r"^\d+\.\d+$", block.get("minimum_api_version", "")):
        err(f"policy {name}: minimum_api_version must be 'maj.min'")


def validate_tdx_policy(name: str, block: dict, platform_slugs: set[str]) -> None:
    unknown = set(block) - TDX_FIELDS
    if unknown:
        err(f"policy {name}: unknown tdx fields {sorted(unknown)}")
    check_hex(f"policy {name}: qe_vendor_id", block.get("qe_vendor_id"), 32)
    check_hex(f"policy {name}: minimum_tee_tcb_svn", block.get("minimum_tee_tcb_svn"), 32)
    check_hex(f"policy {name}: td_attributes", block.get("td_attributes"), 16)
    check_hex(f"policy {name}: xfam", block.get("xfam"), 16)
    check_hex(f"policy {name}: mr_seam", block.get("mr_seam"), 96)
    refs = block.get("platform_measurements", [])
    if not refs:
        err(f"policy {name}: platform_measurements must be non-empty")
    for ref in refs:
        if ref not in platform_slugs:
            err(f"policy {name}: platform_measurements ref {ref!r} not in platforms/")


def validate_shape(slug: str, path: Path) -> None:
    shape = load(path)
    if shape is None:
        return
    if set(shape) != SHAPE_FIELDS:
        err(f"platform {slug}: shape.json must have exactly {sorted(SHAPE_FIELDS)}")
        return
    for k, v in shape.items():
        if not isinstance(v, int) or v < 0:
            err(f"platform {slug}: shape.json {k} must be a non-negative integer, got {v!r}")


def main() -> int:
    root = Path(__file__).parent.parent
    machines = load(root / "machines.json")
    policies = load(root / "policies.json")
    platform_slugs = {p.name for p in (root / "platforms").iterdir() if p.is_dir()}

    for slug in sorted(platform_slugs):
        validate_shape(slug, root / "platforms" / slug / "shape.json")

    if machines is None or policies is None:
        print("\n".join(errors), file=sys.stderr)
        return 1

    for name, policy in policies.items():
        platform = policy.get("platform")
        if platform not in ("sev-snp", "tdx"):
            err(f"policy {name}: invalid platform {platform!r}")
            continue
        block_key = "sev_snp" if platform == "sev-snp" else "tdx"
        if set(policy) != {"platform", block_key}:
            err(f"policy {name}: must contain exactly 'platform' and '{block_key}'")
            continue
        if platform == "sev-snp":
            validate_sev_policy(name, policy[block_key])
        else:
            validate_tdx_policy(name, policy[block_key], platform_slugs)

    for identifier, policy_name in machines.items():
        if not isinstance(policy_name, str):
            err(f"machines[{identifier[:16]}...]: value must be a policy name string "
                "(no metadata objects allowed)")
            continue
        if policy_name not in policies:
            err(f"machines[{identifier[:16]}...]: unknown policy {policy_name!r}")
            continue
        platform = policies[policy_name].get("platform")
        if not HEX_RE.match(identifier or ""):
            err(f"machines key {identifier!r}: not lowercase hex")
        elif platform == "sev-snp":
            if len(identifier) != SEV_ID_LEN:
                err(f"machines[{identifier[:16]}...]: sev-snp identifier must be "
                    f"{SEV_ID_LEN} hex chars (Turin: 16 hex + 112 zeros), got {len(identifier)}")
            elif identifier == "0" * SEV_ID_LEN:
                err("machines: all-zero sev-snp identifier")
        elif platform == "tdx":
            if len(identifier) != PPID_LEN:
                err(f"machines[{identifier[:16]}...]: tdx identifier must be "
                    f"{PPID_LEN} hex chars, got {len(identifier)}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        print(f"\nvalidation FAILED: {len(errors)} error(s)", file=sys.stderr)
        return 1
    print(f"validation OK: {len(machines)} machines, {len(policies)} policies, "
          f"{len(platform_slugs)} platform slugs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
