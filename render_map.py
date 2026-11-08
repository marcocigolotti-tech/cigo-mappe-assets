from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor
from math import atan2,cos,sin

ROOT=Path(__file__).resolve().parent
pdfmetrics.registerFont(TTFont('KalamBold',str(ROOT/'Kalam-Bold.ttf')))
OUT=ROOT/'output'
OUT.mkdir(exist_ok=True)
INK=HexColor('#253548')
YELLOW=HexColor('#FFE56A')
GRAY=HexColor('#66717E')

def label(c,x,y,s,sz=11,center=False,color=INK):
    c.setFillColor(color)
    c.setFont('KalamBold',sz)
    (c.drawCentredString if center else c.drawString)(x,y,s)

def wrap(t,width,sz):
    rows=[]
    line=''
    for word in t.split():
        nxt=(line+' '+word).strip()
        if pdfmetrics.stringWidth(nxt,'KalamBold',sz)<=width:line=nxt
        else:
            if line:rows.append(line)
            line=word
    if line:rows.append(line)
    return rows

def arrow(c,x1,y1,x2,y2):
    c.setLineWidth(1.5);c.setStrokeColor(GRAY);c.setFillColor(GRAY)
    c.line(x1,y1,x2,y2)
    a=atan2(y2-y1,x2-x1)
    p=c.beginPath();p.moveTo(x2,y2)
    for delta in (-.48,.48):
        p.lineTo(x2-6*cos(a+delta),y2-6*sin(a+delta))
    p.close();c.drawPath(p,fill=1,stroke=0)

def draw(data,outfile):
    w,h=landscape(A4)
    c=canvas.Canvas(str(outfile),pagesize=(w,h))
    c.setTitle(data['title']+' — CIGO Mappe')
    c.setAuthor('Prof. Marco Cigolotti')
    c.setFillColor(HexColor('#FFFFFF'));c.rect(0,0,w,h,stroke=0,fill=1)
    label(c,w/2,h-42,data['title'],25,True)
    c.setFillColor(YELLOW);c.roundRect(w/2-165,h-59,330,7,3,fill=1,stroke=0)
    mode=data.get('type','standard')
    label(c,w/2,h-78,'Mappa concettuale — Seconda media — '+mode,11,True,GRAY)
    label(c,w/2,h-119,data.get('root',data['title']),18,True)
    branches=data['branches']
    n=len(branches)
    cw=(w-50)/n
    for i,b in enumerate(branches):
        x=25+i*cw
        cx=x+cw/2
        arrow(c,w/2,h-129,cx,h-175)
        c.setFillColor(YELLOW)
        c.roundRect(x+4,h-204,cw-10,25,5,fill=1,stroke=0)
        label(c,cx,h-196,b['title'],13,True)
        rows=b['items']
        dy=295/max(len(rows),1)
        for j,desc in enumerate(rows):
            y=h-253-j*dy
            c.setFillColor(INK);c.circle(x+14,y+3,2.5,fill=1,stroke=0)
            for k,s in enumerate(wrap(desc,cw-42,11.5)):
                label(c,x+24,y-k*14,s,11.5)
    c.setStrokeColor(HexColor('#DFE4EA'));c.line(24,52,w-24,52)
    label(c,26,34,'Ideato dal Prof. Marco Cigolotti • CIGO Mappe',10,color=GRAY)
    label(c,26,19,'Kalam Bold originale incorporato — licenza SIL OFL 1.1',9,color=GRAY)
    c.save()

for path in sorted((ROOT/'requests').glob('*.json')):
    data=json.loads(path.read_text(encoding='utf-8'))
    target=OUT/(path.stem+'.pdf')
    draw(data,target)
    print('PDF generated',target)
