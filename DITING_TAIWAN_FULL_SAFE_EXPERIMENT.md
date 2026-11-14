# Diting Taiwan / Android 15 / Droidspaces GKI 5.10 — Experimental full-safe build

**Target:** Xiaomi 12T Pro (diting), OS3.0.5.0.VLFTWXM. The previously booted custom Image from workflow run 42532478656 is the known-good rollback baseline.

**Never flash before completing KMI validation and verifying a recoverable boot backup.** This work is experimental; building successfully does not prove phone compatibility.

This branch keeps the reproducible ACK/GKI source, toolchain, original kernel release string, and existing **KernelSU LKM ramdisk**; it must not replace ramdisk or vendor partitions.

## Added options (KMI-gated)
- `CONFIG_NETFILTER_XT_MATCH_ADDRTYPE=y`: required to restore Docker's default bridge NAT rule.
- `CONFIG_USER_NS=y`: Debian/user namespace sandbox support.
- `CONFIG_IP6_NF_NAT=y`, `CONFIG_IP6_NF_TARGET_MASQUERADE=y`: IPv6 NAT.
- `CONFIG_MACVLAN=y`: macvlan networking.
- `CONFIG_NETFILTER_XT_TARGET_LOG=y`, `CONFIG_NETFILTER_XT_MATCH_RECENT=y`: firewall rules.
- `CONFIG_IP_SET=y`, `CONFIG_IP_SET_HASH_IP=y`, `CONFIG_IP_SET_HASH_NET=y`, `CONFIG_NETFILTER_XT_SET=y`: Fail2ban/UFW IP sets.
- `CONFIG_TMPFS_POSIX_ACL=y`, `CONFIG_TMPFS_XATTR=y`: POSIX ACL and xattrs on tmpfs.

If Kconfig does not resolve any requested option to `=y`, or any baseline KMI check fails, the workflow refuses to publish a flash ZIP.

**Must stay OFF:** `CONFIG_CFS_BANDWIDTH`, `CONFIG_CGROUP_PIDS` (Droidspaces official GKI documentation says these break exported symbol CRCs and can bootloop stock vendor modules). Do not disable CFI/SELinux/KMI strictness or force-load vendor modules.

## Intended artifacts
- Tested-only (compile, kernel release, GKI KMI), not yet boot-tested: Image, kernel.config, diagnostic diffs.
- **Candidate** recovery ZIP based on pinned AnyKernel3, replacing only the kernel, keeping the existing boot ramdisk (including KernelSU LKM setup).
- **Known-good kernel rollback** ZIP built from run `42532478656` Image, also AnyKernel3; this recovers the previous booted kernel but does not replace the whole original stock boot image.

**Already on user's phone:** full original boot_a backup and previous TWRP restore ZIP:
`/sdcard/Download/DITING_GERI_DONUS_a_20261113_184012/boot_a_ORIJINAL.img`
`/sdcard/Download/DITING_TWRP_BOOT_a_GERI_DONUS_20261113_184012.zip`.

Original boot SHA256:
`9c5265ea25746d62cb0e4e8b2e5d7e1664cbe706bee77018809e8ca82d0a2be0`.

Always preserve the existing working boot and recovery access. **Never flash a kernel ZIP from an unverified Action run.**
