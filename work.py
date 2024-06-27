from PIL import Image
from urllib.parse import unquote

im = Image.open("test_label.drawio.png")
im.load()
print(unquote(im.info["mxfile"]))
