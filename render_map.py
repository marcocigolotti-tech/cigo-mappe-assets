"""Generate illustrated landscape PDF maps inside GitHub Actions, embedding Kalam Bold."""
from pathlib import Path
from math import atan2,cos,sin
import io,json,urllib.request
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from PIL import Image

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'
OUT.mkdir(exist_ok=True)
pdfmetrics.registerFont(TTFont('KalamBold',str(ROOT/'Kalam-Bold.ttf')))
INK=HexColor('#24364A')
GRAY=HexColor('#57697B')
YELLOW=HexColor('#FFE56A')

def label(c,x,y,s,size=11,center=False,color=INK):
    c.setFillColor(color);c.setFont('KalamBold',size)
    (c.drawCentredString if center else c.drawString)(x,y,s)

def wrap(s,width,size):
    out=[];line=''
    for word in s.split():
        nxt=(line+' '+word).strip()
        if pdfmetrics.stringWidth(nxt,'KalamBold',size)<=width:line=nxt
        else:
            if line:out.append(line)
            line=word
    if line:out.append(line)
    return out

def arrow(c,x1,y1,x2,y2):
    c.setStrokeColor(GRAY);c.setFillColor(GRAY);c.setLineWidth(1.5)
    c.line(x1,y1,x2,y2)
    a=atan2(y2-y1,x2-x1)
    p=c.beginPath();p.moveTo(x2,y2)
    p.lineTo(x2-6*cos(a-.48),y2-6*sin(a-.48))
    p.lineTo(x2-6*cos(a+.48),y2-6*sin(a+.48))
    p.close();c.drawPath(p,fill=1,stroke=0)

def photo(c,d,x,y,w,h):
    uri=d['url']
    cached=ROOT/d.get('asset','__missing_file__')
    if cached.is_file():
        im=Image.open(cached);im.load()
    else:
        if not uri.startswith('https://upload.wikimedia.org/'):
            raise ValueError('Use verified Wikimedia URLs only')
        req=urllib.request.Request(uri,headers={'User-Agent':'CIGO-Mappe/1.0 (educational PDF attribution)'})
        with urllib.request.urlopen(req,timeout=35) as r:raw=r.read()
        im=Image.open(io.BytesIO(raw));im.load()
        if d.get('asset'):
            cached.parent.mkdir(parents=True,exist_ok=True)
            tmp=im.convert('RGB')
            tmp.thumbnail((960,800))
            tmp.save(cached,'JPEG',quality=84,optimize=True)
    if im.mode != 'RGB':im=im.convert('RGB')
    im.thumbnail((960,800))
    packed=io.BytesIO()
    im.save(packed,format='JPEG',quality=83,optimize=True)
    packed.seek(0)
    k=min((w-18)/im.width,(h-12)/im.height)
    iw,ih=im.width*k,im.height*k
    c.drawImage(ImageReader(packed),x+(w-iw)/2,y+(h-ih)/2,iw,ih)
    label(c,x+w/2,y-12,d.get('caption',''),9,True)
    label(c,x+w/2,y-24,d.get('credit',''),7.1,True,GRAY)
    if d.get('source'):c.linkURL(d['source'],(x,y-25,x+w,y+h),relative=0)

def arch(c,x,y,w=76,h=75):
    c.setStrokeColor(INK);c.setLineWidth(3)
    p=c.beginPath();p.moveTo(x,y)
    p.curveTo(x-2,y+34,x+w/4,y+h-18,x+w/2,y+h)
    p.curveTo(x+3*w/4,y+h-18,x+w+2,y+34,x+w,y)
    c.drawPath(p,stroke=1,fill=0)
    label(c,x+w/2,y-14,'Arco a sesto acuto',9.2,True)

def draw(data,dest):
    W,H=landscape(A4)
    c=canvas.Canvas(str(dest),pagesize=(W,H))
    c.setTitle(data['title']+' - CIGO Mappe')
    c.setAuthor('Prof. Marco Cigolotti - CIGO Mappe')
    c.setFillColor(HexColor('#FFFFFF'));c.rect(0,0,W,H,fill=1,stroke=0)
    label(c,W/2,H-43,data['title'],27,True)
    c.setFillColor(YELLOW);c.roundRect(W/2-190,H-61,380,8,4,fill=1,stroke=0)
    facilitated=data.get('type')=='facilitata'
    sub='Mappa concettuale • '+data.get('class_label','Scuola secondaria')+' • '+('versione facilitata' if facilitated else 'versione standard')
    label(c,W/2,H-83,sub,11,True,GRAY)
    label(c,W/2,H-121,data.get('root',data['title']),18,True)
    branches=data['branches'];n=len(branches)
    if not 2<=n<=4:raise ValueError('2-4 branches supported')
    cw=(W-50)/n
    for i,b in enumerate(branches):
        left=25+i*cw;center=left+cw/2
        arrow(c,W/2,H-134,center,H-173)
        c.setFillColor(YELLOW);c.roundRect(left+4,H-205,cw-11,26,6,fill=1,stroke=0)
        label(c,center,H-197,b['title'],14,True)
        for j,desc in enumerate(b['items'][:3]):
            y=H-247-j*66
            c.setFillColor(INK);c.circle(left+14,y+3,2.5,fill=1,stroke=0)
            size=12.6 if facilitated else 11.6
            for q,part in enumerate(wrap(desc,cw-43,size)):
                label(c,left+24,y-q*14,part,size)
    for img in data.get('images',[]):
        i=img['column']
        if not 0<=i<n:raise ValueError('Image column out of range')
        photo(c,img,25+i*cw,95,cw-10,79)
    if data.get('arch_diagram_column') is not None:
        i=data['arch_diagram_column'];arch(c,25+i*cw+cw/2-38,104)
    c.setStrokeColor(HexColor('#DBE0E7'));c.line(25,47,W-25,47)
    label(c,27,31,'Ideato dal Prof. Marco Cigolotti • CIGO Mappe',10,color=GRAY)
    label(c,27,17,'Kalam Bold incorporato • Fotografie: licenze e fonti nelle didascalie',8.2,color=GRAY)
    c.save()

for p in sorted((ROOT/'requests').glob('*.json')):
    data=json.loads(p.read_text(encoding='utf-8'))
    out=OUT/(p.stem+'.pdf')
    draw(data,out)
    print('GENERATED:',out)
