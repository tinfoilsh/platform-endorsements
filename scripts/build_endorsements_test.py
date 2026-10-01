import json
from pathlib import Path
import subprocess
import tempfile
import unittest


class BuildEndorsementsTest(unittest.TestCase):
    def test_igvm_preserves_machine_security_policy_and_legacy_artifact(self):
        root = Path(__file__).resolve().parent.parent
        measurements = {"test-shape": {"mrtd": "a" * 96}}
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            for name in ("scripts", "machines.json", "policies.json", "platform.json", "platforms"):
                (work / name).symlink_to(root / name)
            (work / "hardware-measurements.json").write_text(json.dumps(measurements))
            subprocess.run(["bash", str(root / "scripts/build-endorsements.sh")], cwd=work, check=True, capture_output=True)
            legacy = json.loads((work / "platform-endorsements.json").read_text())
            igvm = json.loads((work / "platform-endorsements-igvm.json").read_text())

        policies = json.loads((root / "policies.json").read_text())
        machines = json.loads((root / "machines.json").read_text())
        self.assertEqual(legacy["measurements"], measurements)
        self.assertEqual(legacy["policies"], policies)
        self.assertEqual(legacy["machines"], machines)
        self.assertEqual(igvm["measurements"], {})
        self.assertEqual(igvm["machines"], machines)
        self.assertEqual(igvm["format"], legacy["format"])
        self.assertEqual(set(igvm["policies"]), set(policies))
        for name, original in policies.items():
            policy = igvm["policies"][name]
            self.assertEqual(policy["platform"], original["platform"])
            block = "sev_snp" if policy["platform"] == "sev-snp" else "tdx"
            moved_field = "host_data" if block == "sev_snp" else "platform_measurements"
            self.assertEqual(policy[block].pop("config_binding"), "sha256")
            self.assertNotIn(moved_field, policy[block])
            self.assertEqual(policy[block], {key: value for key, value in original[block].items() if key != moved_field})


if __name__ == "__main__":
    unittest.main()
