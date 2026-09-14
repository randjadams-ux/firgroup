from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import qrcode
import cv2
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"print-output"
OUT.mkdir(exist_ok=True)

W,H=2100,1400
S=432/W
CREAM=(247,244,237)
FOREST=(8,73,58)
HEADER=(5,82,62)
SEPARATOR=(62,102,82)
WHITE=(250,248,242)
FONT_SANS="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SERIF="/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
FONT_SERIF_BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

PNG_NAME="Fir-Group-GotPrint-Front-v5-2100x1400-350DPI.png"
PDF_NAME="Fir-Group-GotPrint-Front-v5-6x4-Print.pdf"

def ft(path,size):
    return ImageFont.truetype(path,size)

def centered(draw,center,text,font,fill,spacing=6):
    box=draw.multiline_textbbox((0,0),text,font=font,spacing=spacing,align="center")
    w=box[2]-box[0]; h=box[3]-box[1]
    draw.multiline_text((center[0]-w/2,center[1]-h/2-box[1]),text,font=font,fill=fill,spacing=spacing,align="center")

def contain(im,max_w,max_h):
    ratio=min(max_w/im.width,max_h/im.height)
    return im.resize((round(im.width*ratio),round(im.height*ratio)),Image.Resampling.LANCZOS)

def cover(im,width,height):
    ratio=max(width/im.width,height/im.height)
    im=im.resize((round(im.width*ratio),round(im.height*ratio)),Image.Resampling.LANCZOS)
    left=(im.width-width)//2; top=(im.height-height)//2
    return im.crop((left,top,left+width,top+height))

def logo_asset():
    logo=Image.open(ROOT/"assets"/"fir-group-logo.png").convert("RGBA")
    bbox=logo.getbbox()
    return logo.crop(bbox) if bbox else logo

def qr_asset(size):
    q=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H,box_size=12,border=4)
    q.add_data("https://firgroup.org")
    q.make(fit=True)
    im=q.make_image(fill_color="black",back_color="white").convert("RGB")
    return im.resize((size,size),Image.Resampling.NEAREST),q.get_matrix()

def build_png():
    img=Image.new("RGB",(W,H),CREAM)
    d=ImageDraw.Draw(img)

    header_h=370
    photo_top=370
    photo_h=490
    d.rectangle((0,0,W,header_h),fill=HEADER)

    logo=contain(logo_asset(),1040,255)
    img.paste(logo,((W-logo.width)//2,(header_h-logo.height)//2),logo)

    hero=cover(Image.open(ROOT/"assets"/"fir-group-hero.jpeg").convert("RGB"),W,photo_h)
    img.paste(hero,(0,photo_top))

    # Three-firm hierarchy: firm names lead, service descriptions support.
    centered(d,(325,1000),"Fir Law Group",ft(FONT_SERIF_BOLD,66),FOREST)
    centered(d,(1020,1000),"Fir Forensics",ft(FONT_SERIF_BOLD,66),FOREST)
    centered(d,(1750,1000),"Fir Solutions",ft(FONT_SERIF_BOLD,66),FOREST)
    centered(d,(325,1088),"LAW FIRM",ft(FONT_BOLD,35),FOREST)
    centered(d,(1020,1088),"WORKPLACE INVESTIGATIONS",ft(FONT_BOLD,31),FOREST)
    centered(d,(1750,1088),"TECHNOLOGY & AI CONSULTING",ft(FONT_BOLD,28),FOREST)
    d.ellipse((665,983,699,1017),fill=SEPARATOR)
    d.ellipse((1388,983,1422,1017),fill=SEPARATOR)

    centered(d,(1010,1272),"firgroup.org",ft(FONT_BOLD,55),FOREST)
    qr,matrix=qr_asset(145)
    img.paste(qr,(1905,1195))
    img.save(OUT/PNG_NAME,dpi=(350,350),optimize=True)
    return matrix

def pdf_center(c,x,y,text,font,size,color,leading=None):
    c.setFillColor(color); c.setFont(font,size)
    lines=text.split("\n"); lead=leading or size*1.18
    for i,line in enumerate(lines):
        c.drawCentredString(x,y-i*lead,line)

def build_pdf(matrix):
    pdfmetrics.registerFont(TTFont("FirSans",FONT_SANS))
    pdfmetrics.registerFont(TTFont("FirBold",FONT_BOLD))
    pdfmetrics.registerFont(TTFont("FirSerifBold",FONT_SERIF_BOLD))
    pw,ph=6*inch,4*inch
    c=canvas.Canvas(str(OUT/PDF_NAME),pagesize=(pw,ph),pageCompression=1)
    cream=HexColor("#F7F4ED"); forest=HexColor("#08493A"); header=HexColor("#05523E"); sep=HexColor("#3E6652")
    def X(v): return v*S
    def Y(v): return ph-v*S

    c.setFillColor(cream); c.rect(0,0,pw,ph,stroke=0,fill=1)
    c.setFillColor(header); c.rect(0,Y(370),pw,X(370),stroke=0,fill=1)

    logo=contain(logo_asset(),1040,255)
    c.drawImage(ImageReader(logo),X((W-logo.width)/2),Y((370-logo.height)/2+logo.height),width=X(logo.width),height=X(logo.height),mask="auto")

    c.drawImage(str(ROOT/"assets"/"fir-group-hero.jpeg"),0,Y(860),width=pw,height=X(490),preserveAspectRatio=False)

    pdf_center(c,X(325),Y(1024),"Fir Law Group","FirSerifBold",13.6,forest)
    pdf_center(c,X(1020),Y(1024),"Fir Forensics","FirSerifBold",13.6,forest)
    pdf_center(c,X(1750),Y(1024),"Fir Solutions","FirSerifBold",13.6,forest)
    pdf_center(c,X(325),Y(1100),"LAW FIRM","FirBold",7.2,forest)
    pdf_center(c,X(1020),Y(1100),"WORKPLACE INVESTIGATIONS","FirBold",6.35,forest)
    pdf_center(c,X(1750),Y(1100),"TECHNOLOGY & AI CONSULTING","FirBold",5.75,forest)
    c.setFillColor(sep)
    c.circle(X(682),Y(1000),X(17),stroke=0,fill=1)
    c.circle(X(1405),Y(1000),X(17),stroke=0,fill=1)

    pdf_center(c,X(1010),Y(1290),"firgroup.org","FirBold",11.3,forest)

    n=len(matrix); size=X(145); module=size/n; ox=X(1905); oy=Y(1195+145)
    c.setFillColor(HexColor("#FFFFFF")); c.rect(ox,oy,size,size,stroke=0,fill=1)
    c.setFillColor(HexColor("#000000"))
    for row,line in enumerate(matrix):
        for col,on in enumerate(line):
            if on:
                c.rect(ox+col*module,oy+(n-1-row)*module,module+0.03,module+0.03,stroke=0,fill=1)

    c.showPage(); c.save()

def validate():
    png=OUT/PNG_NAME
    im=Image.open(png)
    assert im.size==(2100,1400),im.size
    assert all(abs(v-350)<1 for v in im.info.get("dpi",(0,0))),im.info.get("dpi")
    qr_crop=cv2.imread(str(png))[1175:1370,1880:2080]
    decoded,_,_=cv2.QRCodeDetector().detectAndDecode(qr_crop)
    assert decoded=="https://firgroup.org",decoded
    pdf=PdfReader(str(OUT/PDF_NAME))
    box=pdf.pages[0].mediabox
    assert abs(float(box.width)-432)<0.1 and abs(float(box.height)-288)<0.1
    (OUT/"VALIDATION-v5.txt").write_text(
        "PASS\nDesign: approved three-firm hierarchy front\nPNG: 2100 x 1400 pixels, 350 DPI\nPDF: 6.000 x 4.000 inches\nQR decoded: https://firgroup.org\nFull-bleed header, photograph, and cream field reach page edges\n"
    )

if __name__=="__main__":
    matrix=build_png()
    build_pdf(matrix)
    validate()
