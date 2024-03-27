"""
App User Provisioner

Put a series of user names (one on each line) in a file named `users.csv` in the same
directory as this script. The script will create App Users for each user, using the
project, forms, and other configurations set below. The outputs are one PNG for each
provisioned App User, and a `users.pdf` file with all the App User PNGs in the folder.

Install requirements for this script in `requirements.txt`. The specified versions are
those that were current when the script was last updated, though it should work with
more recent versions. Install these with `pip install -r requirements.txt`.

To run the script, use `python app_user_provisioner.py`.
"""

import base64
import glob
import json
import zlib
from typing import Any

import segno
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pyodk.client import Client

# Customise these settings to your environment.
PROJECT_ID = 149
PROJECT_NAME = "My Cool Project"
FORMS_TO_ACCESS = ["all-widgets", "afp-knowledge"]
ADMIN_PASSWORD = "s00p3rs3cr3t"  # noqa: S105


def get_settings(server_url: str, project_name: str, username: str) -> dict[str, Any]:
    """Template for the settings to encode in the QR image. Customise as needed."""
    return {
        "general": {
            "form_update_mode": "match_exactly",
            "autosend": "wifi_and_cellular",
            "delete_send": True,
            "server_url": server_url,
            "username": username,
        },
        "admin": {
            "admin_pw": ADMIN_PASSWORD,
            "change_server": False,
            "automatic_update": False,
            "change_autosend": False,
        },
        "project": {"name": project_name, "color": "#ffeb3b", "icon": "💥"},
    }


# Check that the Roboto font used for the QR images is available (e.g. on Linux / Win).
try:
    ImageFont.truetype("Roboto-Regular.ttf", 24)
except OSError:
    print(
        "Font file 'Roboto-Regular.ttf' not found. This can be downloaded "
        "from Google, or copied from the Examples directory. "
        "Source: https://fonts.google.com/specimen/Roboto/about"
    )


# Provision the App Users.
with open("users.csv", newline="") as f:
    desired_users = f.readlines()
    desired_users = [user.rstrip() for user in desired_users]

client = Client()
provisioned_users = client.projects.create_app_users(
    display_names=desired_users, forms=FORMS_TO_ACCESS, project_id=PROJECT_ID
)

# Generate the QR codes.
for user in provisioned_users:
    collect_settings = get_settings(
        server_url=f"{client.session.base_url}key/{user.token}/projects/{PROJECT_ID}",
        project_name=f"{PROJECT_NAME}: {user.displayName}",
        username=user.displayName,
    )
    qr_data = base64.b64encode(
        zlib.compress(json.dumps(collect_settings).encode("utf-8"))
    )

    code = segno.make(qr_data, micro=False)
    code.save("settings.png", scale=4)

    png = Image.open("settings.png")
    png = png.convert("RGB")
    text_anchor = png.height
    png = ImageOps.expand(png, border=(0, 0, 0, 30), fill=(255, 255, 255))
    draw = ImageDraw.Draw(png)
    font = ImageFont.truetype("Roboto-Regular.ttf", 24)
    draw.text((20, text_anchor - 10), user.displayName, font=font, fill=(0, 0, 0))
    png.save(f"settings-{user.displayName}.png", format="PNG")

# Concatenate the user images into a PDF.
images = [Image.open(f) for f in sorted(glob.glob("./settings-*.png"))]
if 0 < len(images):
    img = iter(images)
    next(img).save(
        "users.pdf", format="PDF", resolution=100, save_all=True, append_images=img
    )
