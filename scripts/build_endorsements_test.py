import json
from pathlib import Path
import subprocess
import tempfile
import unittest


class BuildEndorsementsTest(unittest.TestCase):
    def test_preserves_machine_security_policy_and_measurements(self):
        root = Path(__file__).resolve().parent.parent
        measurements = {"test-shape": {"mrtd": "a" * 96}}
        policies = json.loads((root / "policies.json").read_text())
        policies["amd-genoa-prod"]["sev_snp"]["minimum_abi_version"] = "2.0"
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            for name in ("scripts", "machines.json", "platform.json", "platforms"):
                (work / name).symlink_to(root / name)
            (work / "hardware-measurements.json").write_text(json.dumps(measurements))
            (work / "policies.json").write_text(json.dumps(policies))
            subprocess.run(["bash", str(root / "scripts/build-endorsements.sh")], cwd=work, check=True, capture_output=True)
            legacy = json.loads((work / "platform-endorsements.json").read_text())

        machines = json.loads((root / "machines.json").read_text())
        self.assertEqual(legacy["measurements"], measurements)
        self.assertEqual(legacy["policies"], policies)
        self.assertEqual(legacy["machines"], machines)
        self.assertEqual(legacy["format"], "https://tinfoil.sh/predicate/platform-endorsements/v1")



if __name__ == "__main__":
    unittest.main()
