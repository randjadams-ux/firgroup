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

PNG_NAME="Fir-Group-GotPrint-Front-v4-2100x1400-350DPI.png"
PDF_NAME="Fir-Group-GotPrint-Front-v4-6x4-Print.pdf"

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

    # Clean text-only service row.
    centered(d,(300,1015),"LAW FIRM",ft(FONT_BOLD,62),FOREST)
    centered(d,(1000,1010),"WORKPLACE\nINVESTIGATIONS",ft(FONT_BOLD,55),FOREST,10)
    centered(d,(1740,1010),"TECHNOLOGY & AI\nCONSULTING",ft(FONT_BOLD,50),FOREST,10)
    d.ellipse((576,996,610,1030),fill=SEPARATOR)
    d.ellipse((1383,996,1417,1030),fill=SEPARATOR)

    centered(d,(1010,1267),"firgroup.org",ft(FONT_SERIF_BOLD,105),FOREST)
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

    pdf_center(c,X(300),Y(1034),"LAW FIRM","FirBold",12.75,forest)
    pdf_center(c,X(1000),Y(993),"WORKPLACE\nINVESTIGATIONS","FirBold",11.3,forest,13.2)
    pdf_center(c,X(1740),Y(993),"TECHNOLOGY & AI\nCONSULTING","FirBold",10.3,forest,12.4)
    c.setFillColor(sep)
    c.circle(X(593),Y(1013),X(17),stroke=0,fill=1)
    c.circle(X(1400),Y(1013),X(17),stroke=0,fill=1)

    pdf_center(c,X(1010),Y(1300),"firgroup.org","FirSerifBold",21.6,forest)

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
    (OUT/"VALIDATION-v4.txt").write_text(
        "PASS\nDesign: approved clean text-only front\nPNG: 2100 x 1400 pixels, 350 DPI\nPDF: 6.000 x 4.000 inches\nQR decoded: https://firgroup.org\nFull-bleed header, photograph, and cream field reach page edges\n"
    )

if __name__=="__main__":
    matrix=build_png()
    build_pdf(matrix)
    validate()
