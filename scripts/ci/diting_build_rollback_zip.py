#!/usr/bin/env python3
"""Build a SELF-CONTAINED TWRP rollback ZIP from the verified diting boot_a backup.

This script runs on the phone (e.g. inside the Droidspaces Debian container).
It never flashes or modifies partitions. It refuses any input except the exact
previously recorded original boot image SHA-256.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

EXPECTED_SHA256 = "9c5265ea25746d62cb0e4e8b2e5d7e1664cbe706bee77018809e8ca82d0a2be0"
DEFAULT_IMAGE = "/storage/emulated/0/Download/DITING_GERI_DONUS_a_20261113_184012/boot_a_ORIJINAL.img"
DEFAULT_OUTPUT = "/storage/emulated/0/Download/DITING_TWRP_GERI_DONUS_ORIJINAL_a_20261114.zip"

UPDATER = r"""#!/sbin/sh
# TWRP-only restoring of a verified full boot_a partition image.
# Device/slot guards are intentional. Never flash a different model/slot.
set -eu
FD="${2:-}"
ZIP="${3:-}"
ui() {
  if [ -n "$FD" ] && [ -e "/proc/self/fd/$FD" ]; then
    printf 'ui_print %s\nui_print\n' "$*" > "/proc/self/fd/$FD"
  fi
  echo "$*"
}
die() { ui "ABORT: $*"; exit 1; }
ui "DITING: verified original boot_a restore"
[ -n "$ZIP" ] && [ -f "$ZIP" ] || die "Missing recovery zip argument"
device_ok=0
for prop in ro.product.device ro.product.vendor.device ro.vendor.product.device ro.build.product; do
  v="$(getprop "$prop" 2>/dev/null || true)"
  case "$v" in diting|diting_*) device_ok=1;; esac
done
[ "$device_ok" = 1 ] || die "Device is not confirmed as diting"
slot="$(getprop ro.boot.slot_suffix 2>/dev/null || true)"
if [ -z "$slot" ]; then slot="$(getprop ro.boot.slot 2>/dev/null || true)"; fi
case "$slot" in a|_a) ;; *) die "Active slot is not confirmed as a ($slot)";; esac
BLOCK=""
for candidate in /dev/block/by-name/boot_a /dev/block/bootdevice/by-name/boot_a; do
  if [ -b "$candidate" ]; then BLOCK="$candidate"; break; fi
done
[ -n "$BLOCK" ] || die "Could not find boot_a block device"
command -v unzip >/dev/null 2>&1 || die "TWRP recovery has no unzip"
command -v sha256sum >/dev/null 2>&1 || die "TWRP recovery has no sha256sum"
TARGET="/tmp/diting_original_boot_a.img"
unzip -p "$ZIP" boot_a_ORIJINAL.img > "$TARGET" || die "Failed to extract backup"
ACTUAL="$(sha256sum "$TARGET" | cut -d ' ' -f 1)"
[ "$ACTUAL" = "9c5265ea25746d62cb0e4e8b2e5d7e1664cbe706bee77018809e8ca82d0a2be0" ] || die "Backup SHA256 mismatch: REFUSING FLASH"
ui "Verified backup SHA256. Flashing boot_a only..."
dd if="$TARGET" of="$BLOCK" bs=4096 || die "Flash failed"
sync
ui "Finished. Boot_a restored. Reboot only after checking for errors."
exit 0
"""

README = """Xiaomi 12T Pro (diting) / Android 15 Taiwan ROM - TWRP BOOT_A ROLLBACK
This archive contains the EXACT full original boot_a.img verified by SHA256.
The installer refuses to flash on any device other than diting or slot other than a.
Expected SHA256: 9c5265ea25746d62cb0e4e8b2e5d7e1664cbe706bee77018809e8ca82d0a2be0

IMPORTANT:
* Recovery must provide unzip, sha256sum, getprop, dd and access to boot_a.
* The active slot MUST be a; do not change slots in order to force-install.
* This restores ONLY boot_a. It will not restore vendor_boot or other partitions.
* A stock boot image can remove root if original ramdisk did not contain root.
* Store a copy externally; internal storage may not decrypt in recovery.
* Keep the previous tested recovery ZIP too.
"""

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=DEFAULT_IMAGE, help="Path to the original boot_a backup")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output portable TWRP rollback ZIP")
    args = parser.parse_args()
    image = Path(args.input)
    target = Path(args.output)
    if not image.is_file():
        parser.error(f"Original boot_a backup not found: {image}")
    digest = hashlib.sha256()
    size = 0
    with image.open("rb") as f:
        while chunk := f.read(4 * 1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    actual = digest.hexdigest()
    if actual != EXPECTED_SHA256:
        parser.error(f"REFUSING: original backup SHA256 mismatch: {actual}")
    if not (8 * 1024 * 1024 <= size <= 256 * 1024 * 1024):
        parser.error(f"REFUSING: unusual boot backup size: {size} bytes")
    if image.resolve() == target.resolve():
        parser.error("Output must not overwrite input image")
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w") as z:
        z.write(image, arcname="boot_a_ORIJINAL.img", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/com/google/android/update-binary", UPDATER)
        z.writestr("META-INF/com/google/android/updater-script", "ui_print(\"DITING rollback\");\n")
        z.writestr("README-RESTORE.txt", README)
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        assert z.read("boot_a_ORIJINAL.img")[:4] != b""
    print(f"CREATED: {target}")
    print(f"SHA256 of embedded boot_a: {actual}")
    print(f"Original size: {size} bytes; ZIP size: {target.stat().st_size} bytes")
    print("No partitions were changed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
