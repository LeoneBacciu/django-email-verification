
import base64
import hashlib
import random
import re
import string

from email.mime.image import MIMEImage

def random_string(length, case="lowercase"):
    return "".join(random.choices(getattr(string, f"ascii_{case}") + string.digits, k=length))

def convert_base64_images(body, attachments):

    def repl(match):
        # Capture subtype in case MIMEImage's use of imghdr.what bugs out in guesesing the file type
        subtype = match.group("subtype")
        key = hashlib.md5(base64.b64decode(match.group("data"))).hexdigest().replace("-", "")
        if key not in base64_images:
           base64_images[key] = {
                "data": match.group("data"),
                "subtype": subtype,
            }
        return ' src="cid:image%s"' % key

    # Compile pattern for base64 inline images
    RE_BASE64_SRC = re.compile(
        r' src="data:image/(?P<subtype>gif|png|jpeg|bmp|webp)(?:;charset=utf-8)?;base64,(?P<data>[A-Za-z0-9|+ /]+={0,2})"',
        re.MULTILINE)

    base64_images = {}

    # Replace and add base64 data to base64_images via repl
    body = re.sub(RE_BASE64_SRC, repl, body)
    for key, image_data in base64_images.items():
        try:
            image = MIMEImage(base64.b64decode(image_data["data"]))
        except TypeError:
            # Check for subtype if checking fails
            if image_data["subtype"]:
                image = MIMEImage(
                    base64.b64decode(image_data["data"]),
                    _subtype=image_data["subtype"]
                )
            else:
                raise
        image.add_header('Content-ID', '<image%s>' % key)
        image.add_header('Content-Disposition', "attachment; filename=%s" % f'image_{random_string(length=6)}')
        attachments.append(image)

    return body, attachments
