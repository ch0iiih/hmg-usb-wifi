"""Exercise refusal, application, and restoration with the real HMG-API engine."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
(ROOT / "host-test").mkdir(exist_ok=True)
PACKAGE = ROOT / "packages/usb-wifi-rtl8822bu"
STOCK = Path(os.environ["HMGAPI_TEST_STOCK"])
CLASSES = Path(os.environ["HMGAPI_ENGINE_CLASSES"])

with tempfile.TemporaryDirectory(prefix="usb-wifi-test-", dir=ROOT / "host-test") as temporary:
    fixture = Path(temporary)
    driver = fixture / "system/wifi/bcmdhd.ko"
    driver.parent.mkdir(parents=True)
    mods = fixture / "data/hmgapi/mods"
    mods.mkdir(parents=True)
    (fixture / "props.txt").write_text("ro.board.platform=tcc803x\n")
    (fixture / "settings.txt").write_text("")
    env = dict(os.environ, HMGAPI_ROOT=str(fixture), HMGAPI_HOST="1",
               HMGAPI_PRODUCT=os.environ.get("HMGAPI_TEST_PRODUCT", "LX2PE.KOR.0000.V039.001.260902"), HMGAPI_ONEBIN="lx2pe")

    def engine(*commands):
        result = subprocess.run(["java", "-cp", str(CLASSES), "hmgapi.engine.Engine", *commands],
                                env=env, text=True, capture_output=True)
        if result.returncode:
            print(result.stdout + result.stderr)
        return result

    archive = ROOT / "dist/usb-wifi-rtl8822bu-0.1.7.zip"
    result = engine("install", str(archive))
    assert result.returncode == 0, result.stdout + result.stderr
    print("PASS signed ZIP imported through the real package installer")

    driver.write_bytes(b"Unexpected baseline")
    before = driver.read_bytes()
    result = engine("apply")
    assert driver.read_bytes() == before
    assert "checksum" in (result.stdout + result.stderr).lower() or hashlib.md5(before).hexdigest() in (result.stdout + result.stderr)
    print("PASS unexpected stock driver refused")

    shutil.copyfile(STOCK, driver)
    # A failed baseline check may have cached a successful probe. Simulate a fresh install.
    probe_cache = fixture / "data/hmgapi/state/probes/usb-wifi-rtl8822bu.json"
    probe_cache.unlink(missing_ok=True)
    conflict = fixture / "data/nemesis/apps/usbwifi.hotspot/svc/usbwifi-hotspot-daemon.sh"
    conflict.parent.mkdir(parents=True)
    conflict.touch()
    result = engine("apply")
    assert "probe failed" in (result.stdout + result.stderr)
    assert driver.read_bytes() == STOCK.read_bytes()
    print("PASS active legacy package refused")
    conflict.unlink()

    result = engine("apply")
    assert result.returncode == 0, result.stdout + result.stderr
    assert driver.read_bytes() == (PACKAGE / "files/bcmdhd-rtl8822bu.ko").read_bytes()
    print("PASS candidate driver applied")

    result = engine("restore")
    assert result.returncode == 0, result.stdout + result.stderr
    assert driver.read_bytes() == STOCK.read_bytes()
    print("PASS exact original driver restored")
