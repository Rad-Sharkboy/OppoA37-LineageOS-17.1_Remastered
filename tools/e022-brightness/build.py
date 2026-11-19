"""Build E022's replacement for the installed E016 brightness overlay."""
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

src = Path(__file__).resolve().parent
lab = Path("/home/faizan/a37-e007")
base = lab / "e016"
aapt = base / "tools/aapt2"
framework = base / "framework-res.apk"
prior = base / "brightness/A37Brightness.apk"
output = lab / "e022-brightness"
relative = Path("system/product/overlay/A37Brightness/A37Brightness.apk")
apk = output / "payload" / relative


def run(*args):
    return subprocess.check_output(args, text=True)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resources(path):
    return run(aapt, "dump", "resources", path)


def verify_arrays(table, bright, dark):
    for name, value in (("Brightening", bright), ("Darkening", dark)):
        pattern = rf"array/config_ambient{name}Thresholds\b[^\n]*\n\s+\(\) \(array\) size=1\n\s+\[{value}\]"
        if not re.search(pattern, table):
            raise ValueError(f"Unexpected ambient {name.lower()} threshold")


old = resources(framework)
verify_arrays(old, 100, 200)
if not re.search(r"array/config_ambientThresholdLevels\b[^\n]*\n\s+\(\) \(array\) size=0", old):
    raise ValueError("Unexpected ambient lux buckets")
apk.parent.mkdir(parents=True, exist_ok=True)
password = base / "keys/password"
with tempfile.TemporaryDirectory(prefix="a37-e022-overlay-") as tmp:
    work = Path(tmp)
    run(aapt, "compile", "--dir", src / "res", "-o", work / "res.zip")
    run(aapt, "link", "-I", framework, "--manifest", src / "AndroidManifest.xml",
        "--auto-add-overlay", "-o", work / "unsigned.apk", work / "res.zip")
    run("jarsigner", "-keystore", base / "keys/overlay.jks", "-storepass:file", password,
        "-keypass:file", password, "-sigalg", "SHA256withRSA", "-digestalg", "SHA-256",
        "-signedjar", work / "signed.apk", work / "unsigned.apk", "a37_overlay")
    run("zipalign", "-f", "4", work / "signed.apk", apk)
run("zipalign", "-c", "4", apk)
if "jar verified." not in run("jarsigner", "-verify", apk):
    raise ValueError("Overlay signature verification failed")


def cert_fingerprint(path):
    cert = run("keytool", "-printcert", "-jarfile", path)
    return re.findall(r"SHA256:\s+([0-9A-F:]+)", cert)


old_certificate = cert_fingerprint(prior)
if not old_certificate or cert_fingerprint(apk) != old_certificate:
    raise ValueError("Brightness overlay signing certificate differs")
table = resources(apk)
verify_arrays(table, 200, 300)
if len(re.findall(r"^\s+resource 0x", table, re.M)) != 3 or not re.search(
        r"integer/config_autoBrightnessDarkeningLightDebounce\b[^\n]*\n\s+\(\) 8000\b", table):
    raise ValueError("Unexpected brightness payload resources")
profile = {
    "ambient_hysteresis_per_mille": [200, 300],
    "system_edits": {
        relative.as_posix(): {
            "base_sha256": digest(prior),
            "sha256": digest(apk),
            "uid": 0, "gid": 0, "mode": 0o644,
            "selabel": "u:object_r:vendor_overlay_file:s0",
        }
    },
}
(output / "profile.json").write_text(json.dumps(profile, indent=2) + "\n")
print("Brightness overlay built and verified. Ambient thresholds 20% / 30%, darkening debounce 8 s.")
