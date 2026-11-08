#!/usr/bin/env python3
"""CIGO Mappe 1.9 - Recupera Kalam Bold da risorse locali o Google Fonts.
La risorsa remota e' verificata tramite Git blob SHA; il download richiede
accesso alla rete nel runtime. Non fa affidamento sulla sola presenza nel plugin.
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import tarfile
import urllib.request
import urllib.error
import zipfile
from pathlib import Path

FONT_NAME = 'Kalam-Bold.ttf'
CACHE = Path('/mnt/data/.cigo-mappe/fonts/Kalam-Bold.ttf')
ROOT = Path(__file__).resolve().parent.parent
GOOGLE_FONT_URL = 'https://raw.githubusercontent.com/google/fonts/main/ofl/kalam/Kalam-Bold.ttf'
GOOGLE_FONT_BLOB_SHA = '321272d977887fefb4911789a2691d3131d1bcf0'
# Il file storico incluso nel plugin e' valido, seppure non identico al file di Google Fonts.
HISTORIC_SHA256 = 'f2b5f6595f274a4bb00777fd7cb2958fa837ac7bf266a9c3f7d724ca01013c95'


def validate(data):
    if len(data) < 100_000 or data[:4] not in (b'\x00\x01\x00\x00', b'OTTO', b'true'):
        return False
    try:
        from fontTools.ttLib import TTFont
        import io
        font = TTFont(io.BytesIO(data))
        names = font['name'].names
        name_str = [n.toUnicode().lower() for n in names if n.nameID in (1,2,4,6)]
        return any('kalam' in n for n in name_str) and any('bold' in n for n in name_str)
    except ImportError:
        # In assenza di fontTools il controllo finale e' demandato a ReportLab.
        return True
    except Exception:
        return False


def valid_file(path):
    try:
        return Path(path).is_file() and validate(Path(path).read_bytes())
    except OSError:
        return False


def cache_bytes(data):
    if not validate(data):
        raise ValueError('Il file ricevuto non e un font Kalam Bold valido')
    CACHE.parent.mkdir(parents=True,exist_ok=True)
    tmp=CACHE.with_suffix('.tmp')
    tmp.write_bytes(data)
    tmp.replace(CACHE)
    return CACHE


def unpack_font(archive):
    try:
        if zipfile.is_zipfile(archive):
            with zipfile.ZipFile(archive) as f:
                names=[n for n in f.namelist() if n.endswith('/'+FONT_NAME)]
                data=f.read(min(names,key=len)) if names else b''
        elif tarfile.is_tarfile(archive):
            with tarfile.open(archive,'r:*') as f:
                members=[m for m in f.getmembers() if m.isfile() and m.name.endswith('/'+FONT_NAME)]
                member=f.extractfile(min(members,key=lambda m:len(m.name))) if members else None
                data=member.read() if member else b''
        else:return None
        return cache_bytes(data) if data else None
    except (OSError, ValueError,tarfile.TarError,zipfile.BadZipFile):
        return None


def git_blob_sha(data):
    return hashlib.sha1((f'blob {len(data)}\0').encode('ascii')+data).hexdigest()


def download_official():
    req=urllib.request.Request(GOOGLE_FONT_URL,headers={'User-Agent':'CIGO-Mappe/1.9'})
    with urllib.request.urlopen(req,timeout=15) as r:
        data=r.read(2_000_001)
    if git_blob_sha(data)!=GOOGLE_FONT_BLOB_SHA:
        raise ValueError('Impronta del font remoto differente da quella verificata')
    return cache_bytes(data)


def resolve_font(font_path=None,archive=None,allow_network=True):
    candidates=[]
    if font_path:candidates.append(Path(font_path))
    if os.getenv('CIGO_KALAM_FONT'):candidates.append(Path(os.environ['CIGO_KALAM_FONT']))
    candidates += [ROOT/'assets/fonts'/FONT_NAME,Path.cwd()/FONT_NAME,Path('/mnt/data')/FONT_NAME,CACHE]
    if Path('/mnt/data').is_dir():candidates+=list(Path('/mnt/data').glob('Kalam-Bold*.ttf'))
    for p in candidates:
        if valid_file(p):return p.resolve(),'locale'
    archives=[]
    if archive:archives.append(Path(archive))
    if os.getenv('CIGO_PLUGIN_ARCHIVE'):archives.append(Path(os.environ['CIGO_PLUGIN_ARCHIVE']))
    for folder in (Path('/mnt/data'),Path.cwd()):
        if folder.is_dir():archives += [p for p in folder.iterdir() if p.is_file() and p.name.lower().endswith(('.zip','.tar.gz','.tgz'))]
    for p in dict.fromkeys(archives):
        result=unpack_font(p)
        if result:return result.resolve(),f'archivio {p.name}'
    if allow_network:
        try:
            result=download_official()
            return result.resolve(),'Google Fonts (GitHub pubblico, impronta verificata)'
        except (OSError,ValueError,urllib.error.URLError) as exc:
            raise FileNotFoundError('Font non reperibile localmente; download remoto non riuscito: '+str(exc)+'. '
                'Il runtime potrebbe non avere accesso HTTP a GitHub. Nessuna sostituzione del font viene fatta.') from exc
    raise FileNotFoundError('Kalam Bold non trovato localmente; scaricamento remoto disabilitato')


def verify_pdf(pdf):
    exe=shutil.which('pdffonts')
    if not exe:print('ATTENZIONE: pdffonts non disponibile, incorporamento non verificato esternamente');return
    p=subprocess.run([exe,str(pdf)],capture_output=True,text=True,check=True)
    lines=[line for line in p.stdout.splitlines() if 'Kalam' in line]
    if not lines or not any('yes' in line.lower() for line in lines):
        raise RuntimeError('Font Kalam non incorporato correttamente: '+p.stdout)
    print('PDFFONTS: EMBEDDED OK')


def make_test_pdf(path,font):
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4,landscape
    pdfmetrics.registerFont(TTFont('CIGO-Kalam-Bold',str(font)))
    dest=Path(path);dest.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(dest),pagesize=landscape(A4))
    c.setFont('CIGO-Kalam-Bold',26);c.drawString(48,535,'CIGO MAPPE 1.9 - TEST FONT')
    c.setFont('CIGO-Kalam-Bold',17);c.drawString(48,492,'ARTE GOTICA - archi, vetrate, luce')
    c.setFont('CIGO-Kalam-Bold',12);c.drawString(48,452,'Kalam Bold incorporato e testo selezionabile')
    c.save()
    verify_pdf(dest)
    print('PDF_TEST:',dest)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--test-pdf',type=Path,required=True)
    parser.add_argument('--font-path',type=Path)
    parser.add_argument('--archive',type=Path)
    parser.add_argument('--no-network',action='store_true')
    args=parser.parse_args()
    font,origin=resolve_font(args.font_path,args.archive,not args.no_network)
    print('FONT:',font,'ORIGINE:',origin)
    make_test_pdf(args.test_pdf,font)


if __name__=='__main__':main()
