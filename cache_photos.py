"""Cache two Wikimedia Commons photos from the already verified PDF output.

This avoids repeated downloads that Wikimedia may rate-limit. Source photos
and CC BY-SA credits are documented in requests/arte-gotica-standard.json.
"""
from pathlib import Path
from io import BytesIO
import fitz
from PIL import Image

ROOT=Path(__file__).resolve().parent
source=ROOT/'output/arte-gotica-standard.pdf'
dest=ROOT/'assets'
files=[dest/'chartres.jpg',dest/'sainte-chapelle.jpg']
if all(p.is_file() for p in files):
    print('Photographs already cached')
elif source.exists():
    dest.mkdir(exist_ok=True)
    doc=fitz.open(source)
    images=doc[0].get_images(full=True)
    if len(images)<2:
        raise RuntimeError('Expected two verified photos in original PDF')
    for target,info in zip(files,images[:2]):
        item=doc.extract_image(info[0])
        img=Image.open(BytesIO(item['image']))
        if img.mode!='RGB':img=img.convert('RGB')
        img.thumbnail((960,800))
        img.save(target,'JPEG',quality=84,optimize=True)
        print('PHOTO CACHED:',target, target.stat().st_size)
    doc.close()
else:
    print('No source PDF to recover photos from')
