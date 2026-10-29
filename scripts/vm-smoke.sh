#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
image=.tools/vm/ubuntu-24.04-minimal-20261027-amd64.img
export TMPDIR="$PWD/.tools/vm"
mkdir -p evidence
echo '3839f148c5a3b4a736e7dbb0af75594743fa5ebee2a202424ba1a32e5d3b5d2c  '"$image" | sha256sum -c -
genisoimage -quiet -output .tools/vm/seed.iso -volid cidata -joliet -rock \
  integration/vm-seed/user-data integration/vm-seed/meta-data integration/vm-seed/network-config
timeout 360 qemu-system-x86_64 \
  -machine accel=tcg -cpu max -m 1536 -smp 2 \
  -display none -serial file:evidence/vm-boot.log -monitor none \
  -nic none -snapshot \
  -drive "file=$image,format=qcow2,if=virtio" \
  -drive file=.tools/vm/seed.iso,format=raw,media=cdrom -no-reboot
rg SAFETY_VM_READY evidence/vm-boot.log
