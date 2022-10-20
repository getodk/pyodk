from pyodk.client import Client

import base64
import json
import glob
import segno
from typing import Optional
import zlib
from PIL import Image, ImageOps, ImageFont, ImageDraw

# Put a series of names in a file named users.csv in this directory to create their App Users on a server as configured below.
# The outputs are one PNG for each newly-provisioned App User and a single PDF with all of the App User pngs in the folder.

PROJECT = 149
PROJECT_NAME = "My Cool Project"
FORMS_TO_ACCESS = ["all-widgets", "afp-knowledge"]
APP_USER_ROLE_ID = 2

COLLECT_SETTINGS = { 
  "general": {
    "form_update_mode": "match_exactly",
    "autosend": "wifi_and_cellular",
    "delete_send": True
  },
  "admin": {
 	"admin_pw": "s00p3rs3cr3t",
    "change_server": False,
    "automatic_update": False,
    "change_autosend": False
  },
  "project": {
      "color": "#ffeb3b",
      "icon": "💥"
  }
}

client = Client().open()

with open('users.csv', newline='') as f:
    desired_users = f.readlines()
    desired_users = [user.rstrip() for user in desired_users]

current_users = client.get(f"/projects/{PROJECT}/app-users").json()
current_users = [user for user in current_users if user["token"] is not None]

current_display_names = [user['displayName'] for user in current_users]
to_provision = set(desired_users) - set(current_display_names)

for user in to_provision:
    print("Provisioning: " + user)
    try:
        provision_resp = client.post(f"projects/{PROJECT}/app-users", json={"displayName": user})
        provision_resp.raise_for_status()
    except Exception as err:
        print(err)

    user_id = provision_resp.json()['id']

    for formid in FORMS_TO_ACCESS:
        try:    
            assignment_resp = client.post(f"projects/{PROJECT}/forms/{formid}/assignments/{APP_USER_ROLE_ID}/{user_id}")
            assignment_resp.raise_for_status()
        except Exception as err:
            print(err)

    # Customize the QR code
    url = f"https://{client.auth.session.base_url}key/{provision_resp.json()['token']}/projects/{PROJECT}"
    COLLECT_SETTINGS["general"]["server_url"] = url
    COLLECT_SETTINGS["project"]["name"] = f"{PROJECT_NAME}: {user}"
    COLLECT_SETTINGS["general"]["username"] = user
    
    qr_data = base64.b64encode(zlib.compress(json.dumps(COLLECT_SETTINGS).encode("utf-8")))

    code = segno.make(qr_data, micro=False)
    code.save("settings.png", scale=4)

    png = Image.open('settings.png')
    png = png.convert('RGB')
    text_anchor = png.height
    png = ImageOps.expand(png, border=(0, 0, 0, 30), fill = (255, 255, 255))
    draw = ImageDraw.Draw(png)
    font = ImageFont.truetype("Roboto-Regular.ttf", 24)
    draw.text((20, text_anchor - 10), user, font = font, fill = (0, 0, 0))
    png.save(f"settings-{user}.png", format = 'PNG')

images = [Image.open(f) for f in glob.glob('./settings-*.png')]

images[0].save("pdf", "PDF", resolution=100, save_all=True, append_images=images[1:])
