#!/bin/sh
ROOTFS_PATH=$1
if [ -z "$ROOTFS_PATH" ]; then
    echo "Usage: $0 <path-to-rootfs>"
    exit 1
fi

rsync -av --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' ./rootfs/buildroot/ "$ROOTFS_PATH/"
rsync -av --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='rootfs' --exclude='resources' ./ "$ROOTFS_PATH/root/PS4JB"

# Configure USB device
sed -i '/^UMS_EN=/s/off$/on/' "$ROOTFS_PATH/etc/init.d/S50usbdevice"

echo "Repackaging firmware required with new rootfs. Run \`./build.sh firmware\` on luckfox-pico SDK directory"
