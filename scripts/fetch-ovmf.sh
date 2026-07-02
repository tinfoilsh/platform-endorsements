#!/bin/bash

set -ex

echo "Fetching OVMF.fd"
expected_hash="9e807cb2cd4313406a3aa4becc0836671a5c64ca7bdc08a45e15260184b446bf"
wget -q http://archive.ubuntu.com/ubuntu/pool/main/e/edk2/ovmf_2025.02-3ubuntu2_all.deb -O ovmf.deb

# make tmp dir to extract the deb file
mkdir -p ovmf_tmp
dpkg-deb -R ovmf.deb ovmf_tmp

# copy the OVMF.fd file to the current directory
cp ovmf_tmp/usr/share/ovmf/OVMF.fd .

rm -rf ovmf.deb ovmf_tmp

# Check that hash matches
if [ "$expected_hash" != "$(sha256sum OVMF.fd | awk '{print $1}')" ]; then
    echo "Hash mismatch"
    exit 1
else
    echo "Hash matches"
fi

echo "OVMF fetched successfully"
