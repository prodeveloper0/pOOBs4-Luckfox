import os
import time
import logging
import socket
import json

import click

from pathlib import Path

from flask import Flask, send_from_directory, jsonify, request, redirect


app = Flask(__name__, static_folder=None)

current_files_dir = Path(os.getcwd())
static_files_dir = current_files_dir / "static"
is_debug = False
redirect_url = None

ums_delay = 15.


def enable_mass_storage(blkdev: str, ro: bool = True):
    # Only works in Luckfox
    if is_debug:
        return

    blk_file_path = "/sys/kernel/config/usb_gadget/rockchip/functions/mass_storage.0/lun.0/file"
    ro_file_path = "/sys/kernel/config/usb_gadget/rockchip/functions/mass_storage.0/lun.0/ro"

    with open(ro_file_path, "w") as f:
        f.write("1" if ro else "0")

    with open(blk_file_path, "w") as f:
        f.write(f"{blkdev}\n")


def disable_mass_storage():
    # Only works in Luckfox
    if is_debug:
        return
    
    path = "/sys/kernel/config/usb_gadget/rockchip/functions/mass_storage.0/lun.0/file"
    with open(path, "w") as f:
        f.write("")


def send_payload(path: str, host: str, port: int):
    # Implement netcat-like functionality to send a file over TCP
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=0)
    s.settimeout(3000)
    s.connect((host, port))

    try:
        with open(path, "rb") as fp:
            s.sendfile(fp)
    finally:
        s.close()


@app.route("/api/<path:path>", methods=["POST"])
def catch_api_routes(path: str):
    params = request.args.to_dict()

    def disable_etho0():
        logging.error("Disable eth0 interface...")
        if not is_debug:
            os.system("ifconfig eth0 down")
            exit(0)

    def shutdown():
        # TODO Shutting down or rebooting the system not working properly with UMS gadget
        logging.error("Shutting down the system...")
        if not is_debug:
            os.system("halt")
            exit(0)

    def plug_exfathax():
        logging.error("Enable UMS (USB Mass Storage)...")
        enable_mass_storage(static_files_dir / "exfathax.img", ro=True)

    def unplug_exfathax():
        logging.error("Disable UMS (USB Mass Storage)...")
        disable_mass_storage()

    def send_main_payload():
        logging.error("Sending main payload...")
        ps4_addr = request.remote_addr
        loader_port = 9020
        time.sleep(5)
        send_payload(static_files_dir / "payload.bin", ps4_addr, loader_port)

    def emulate_exfathax():
        delay = float(params.get("delay", max(ums_delay, 0)))
        logging.error(f"Emulating USB mass storage for ExFatHax... delay={delay} seconds")
        enable_mass_storage(static_files_dir / "exfathax.img", ro=True)
        time.sleep(delay)
        disable_mass_storage()
        time.sleep(1)

    def server_sleep():
        time.sleep(float(params.get("seconds", 0)))
    
    if path == "disable-eth0":
        disable_etho0()
    elif path == "shutdown":
        shutdown()
    elif path == "plug-exfathax":
        plug_exfathax()
    elif path == "unplug-exfathax":
        unplug_exfathax()
    elif path == "send-main-payload":
        send_main_payload()
    elif path == "emulate-exfathax":
        emulate_exfathax()
    elif path == "server-sleep":
        server_sleep()

    return jsonify({"path": path})


@app.route("/", methods=["GET"])
@app.route("/<path:path>", methods=["GET"])
def catch_all_routes(path: str = "index.html"):
    if redirect_url and "playstation.net" in request.host:
        return redirect(redirect_url)

    if path == "":
        path = "index.html"

    file_path = static_files_dir / path
    if os.path.isdir(file_path):
        file_path = file_path / "index.html"
    
    return send_from_directory(file_path.parent, file_path.name)


@click.command()
@click.option("--host", default="0.0.0.0", help="Host to run the server on")
@click.option("--port", default=9191, help="Port to run the server on")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--redirect-playstation-domain", default=None, type=str, help="Redirect *.playstation.net domain to other URL")
def main(host: str, port: int, debug: bool, redirect_playstation_domain: str):
    global is_debug, redirect_url
    is_debug = debug
    redirect_url = redirect_playstation_domain
    with open(current_files_dir / "config.json", "r") as f:
        config = json.load(f)
        global ums_delay
        ums_delay = config.get("ums_delay", 15.)

    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    main()
