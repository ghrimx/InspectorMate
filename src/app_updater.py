import requests, subprocess, sys, os

from utilities.config import config

def check_update():
    try:
        latest = requests.get("https://example.com/latest.json").json()
    except Exception as e:
        print(e)
        return

    if latest["version"] != config.app_version:
        print("Update available:", latest["version"])
        installer = f"inspectormate-{latest["version"]}.exe"
        r = requests.get(latest["url"])
        with open(installer, "wb") as f:
            f.write(r.content)
        print("Running installer...")
        subprocess.Popen([installer, "/VERYSILENT"])
        sys.exit(0)  # close app before update

if __name__ == "__main__":
    check_update()
    # continue running app
