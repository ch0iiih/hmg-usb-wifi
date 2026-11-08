"""Run the monitor against synthetic USB/sysfs files without accessing real devices."""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
(ROOT / "host-test").mkdir(exist_ok=True)
SOURCE = ROOT / "packages/usb-wifi-rtl8822bu/svc/driver-event.sh"


def run_case(name, connected=False, unplug=False, insmod_failure=False, reconnect=False, rebind=False, bound=False):
    with tempfile.TemporaryDirectory(prefix="monitor-", dir=ROOT / "host-test") as temporary:
        fixture = Path(temporary)
        mock = fixture / "mock"
        mock.mkdir()
        for directory in ["sys/bus/usb/devices", "sys/class/net", "sys/module/tcc_dwc_otg/parameters",
                          "proc/sys/kernel/random", "system/wifi", "storage/usb0/USB-WIFI-LOGS"]:
            (fixture / directory).mkdir(parents=True)
        power = fixture / "sys/module/tcc_dwc_otg/parameters/vbus_control_enable"
        power.write_text("1\n")
        (fixture / "proc/sys/kernel/random/boot_id").write_text("test-boot\n")
        (fixture / "proc/modules").write_text("")
        device = fixture / "sys/bus/usb/devices/1-1"
        if connected:
            device.mkdir()
            (device / "idVendor").write_text("2357\n")
            (device / "idProduct").write_text("012e\n")

        if rebind:
            interface = device / "1-1:1.0"
            interface.mkdir()
            (interface / "bInterfaceClass").write_text("ff\n")
            if bound: (interface / "driver").mkdir()
            driver = fixture / "sys/bus/usb/drivers/rtl88x2bu"
            driver.mkdir(parents=True)
            (driver / "bind").touch()

        scripts = {
            "getprop": "echo LX2PE.KOR.0000.V039.001.260902\n",
            "logcat": "echo framework-test\n",
            "dmesg": "echo 'rtl88x2bu synthetic log'\n",
            "ip": "exit 0\n",
            "sync": "exit 0\n",
            "insmod": f'echo "$*" >> "$FIXTURE/insmod-calls"\n' + ('mkdir -p "$FIXTURE/sys/module/bcmdhd"\n' if not insmod_failure else '') + f'exit {int(insmod_failure)}\n',
            "sleep": 'touch "$FIXTURE/unexpected-sleep"\nexit 99\n',

        }
        for command, body in scripts.items():
            path = mock / command
            path.write_text("#!/bin/sh\n" + body)
            path.chmod(0o755)
        source = SOURCE.read_text()
        source = source.replace(next(line for line in source.splitlines() if line.startswith("export PATH=")),
                                f"export PATH={mock}:/usr/bin:/bin:/usr/sbin:/sbin")
        for prefix in ["/data/", "/sys/", "/proc/", "/storage/", "/system/"]:
            source = source.replace(prefix, str(fixture) + prefix)
        script = fixture / "monitor.sh"
        script.write_text(source)
        env = dict(os.environ, FIXTURE=str(fixture), UNPLUG=str(int(unplug)))
        def invoke(action):
            result = subprocess.run(["/bin/sh", str(script), action], env=env,
                                    capture_output=True, text=True, timeout=15)
            assert result.returncode == 0, result.stdout + result.stderr

        invoke("startup")
        assert power.read_text().strip() == ("0" if connected else "1")
        if rebind:
            for _ in range(5): invoke("repair")
            count = fixture / "data/local/tmp/hmg-usb-wifi-rtl8822bu/repair-count"
            if bound:
                assert not count.exists()
            else:
                assert count.read_text().strip() == "3"
                assert (fixture / "sys/bus/usb/drivers/rtl88x2bu/bind").read_text().strip() == "1-1:1.0"
                (fixture / "sys/class/net/wlan0").mkdir()
                invoke("repair")
                assert count.read_text().strip() == "3"
        invoke("snapshot")
        invoke("update")
        if connected:
            power.write_text("1\n")
            invoke("guard")
            assert power.read_text().strip() == "0"
        if unplug:
            import shutil
            shutil.rmtree(device)
            invoke("detach")
            assert power.read_text().strip() == "1"
        if reconnect:
            device.mkdir()
            (device / "idVendor").write_text("2357\n")
            (device / "idProduct").write_text("012e\n")
            invoke("update")
            assert power.read_text().strip() == "0"
        invoke("shutdown")
        calls = fixture / "insmod-calls"
        call_lines = calls.read_text().splitlines() if calls.exists() else []
        assert len(call_lines) == int(connected), (name, call_lines)
        assert power.read_text().strip() == "1", name
        assert not (fixture / "unexpected-sleep").exists(), "The script must not poll or sleep"
        logs = fixture / "storage/usb0/USB-WIFI-LOGS"
        assert "finished=1" in (logs / "current.txt").read_text()
        if connected:
            saved = fixture / "data/local/tmp/hmg-usb-wifi-rtl8822bu/last-adapter.txt"
            assert "idProduct\n012e" in saved.read_text()
        print("PASS", name)



run_case("no adapter leaves port control and module state alone")
run_case("adapter loads once and service shutdown restores port control", connected=True)
run_case("unplug restores port control and retains the connected snapshot", connected=True, unplug=True)
run_case("failed module load is recorded without a retry loop", connected=True, insmod_failure=True)

run_case("repeated unplug and replug reuses the loaded driver", connected=True, unplug=True, reconnect=True)

run_case("unbound interface retry stops at three and skips a ready interface", connected=True, rebind=True)
run_case("bound interfaces are never rebound", connected=True, rebind=True, bound=True)
