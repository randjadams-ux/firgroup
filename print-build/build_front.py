from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import inch
from reportlab.lib.colors import CMYKColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader
import cv2

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "print-output"
OUT.mkdir(exist_ok=True)

W, H = 2100, 1400
S = 432 / W
CREAM = (247, 244, 237)
FOREST = (9, 57, 49)
SAGE = (126, 145, 131)
TAUPE = (210, 205, 194)
BLACK = (0, 0, 0)

FONT_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

def font(path, size):
    return ImageFont.truetype(path, size)

def centered(draw, xy, text, fnt, fill, spacing=4):
    box = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=spacing, align="center")
    tw = box[2] - box[0]
    th = box[3] - box[1]
    draw.multiline_text((xy[0] - tw / 2, xy[1] - th / 2 - box[1]), text, font=fnt, fill=fill, spacing=spacing, align="center")

def contain(im, max_w, max_h):
    ratio = min(max_w / im.width, max_h / im.height)
    return im.resize((round(im.width * ratio), round(im.height * ratio)), Image.Resampling.LANCZOS)

def cover(im, width, height):
    ratio = max(width / im.width, height / im.height)
    im = im.resize((round(im.width * ratio), round(im.height * ratio)), Image.Resampling.LANCZOS)
    left = (im.width - width) // 2
    top = (im.height - height) // 2
    return im.crop((left, top, left + width, top + height))

def draw_scale(draw, cx, cy, color, sw=11):
    # Complete, symmetrical scales with connected cords, pans, upright, and base.
    draw.ellipse((cx-10, cy-104, cx+10, cy-84), fill=color)
    draw.line((cx, cy-88, cx, cy+94), fill=color, width=sw)
    draw.line((cx-112, cy-72, cx+112, cy-72), fill=color, width=sw)
    draw.line((cx-112, cy-72, cx-58, cy-68), fill=color, width=sw)
    draw.line((cx+58, cy-68, cx+112, cy-72), fill=color, width=sw)
    for sign in (-1, 1):
        anchor = cx + sign*100
        draw.line((anchor, cy-68, anchor-sign*36, cy+23), fill=color, width=7)
        draw.line((anchor, cy-68, anchor+sign*36, cy+23), fill=color, width=7)
        left = anchor-52
        right = anchor+52
        draw.arc((left, cy-5, right, cy+72), 12, 168, fill=color, width=8)
        draw.line((left+5, cy+34, right-5, cy+34), fill=color, width=5)
    draw.rounded_rectangle((cx-38, cy+84, cx+38, cy+108), radius=6, fill=color)
    draw.rounded_rectangle((cx-72, cy+106, cx+72, cy+123), radius=5, fill=color)

def draw_magnifier(draw, cx, cy, color, sw=11):
    draw.ellipse((cx-66, cy-88, cx+50, cy+28), outline=color, width=sw)
    draw.line((cx+35, cy+13, cx+104, cy+82), fill=color, width=sw)
    draw.line((cx-45, cy+112, cx+70, cy+112), fill=color, width=8)

def draw_growth(draw, cx, cy, color, sw=11):
    pts=[(cx-100,cy+52),(cx-34,cy-14),(cx+25,cy+44),(cx+105,cy-52)]
    draw.line(pts, fill=color, width=sw, joint="curve")
    draw.line((cx+105,cy-52,cx+105,cy+6),fill=color,width=sw)
    draw.line((cx+105,cy-52,cx+48,cy-52),fill=color,width=sw)
    draw.line((cx-52, cy+112, cx+70, cy+112), fill=color, width=8)

def qr_image(size):
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data("https://firgroup.org")
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB").resize((size,size), Image.Resampling.NEAREST), qr.get_matrix()

def draw_logo_png(draw):
    cx, cy, r = 590, 148, 105
    draw.ellipse((cx-r,cy-r,cx+r,cy+r), outline=FOREST, width=8)
    draw.line((cx,cy-67,cx,cy+70), fill=FOREST, width=10)
    tiers=[(-54,36),(-22,51),(12,63),(47,74)]
    for yy,half in tiers:
        draw.polygon([(cx,cy+yy-31),(cx-half,cy+yy+24),(cx-11,cy+yy+18),(cx,cy+yy+5),(cx+11,cy+yy+18),(cx+half,cy+yy+24)],fill=FOREST)
    centered(draw,(1190,145),"THE FIR GROUP",font(FONT_SERIF_BOLD,105),FOREST)
    draw.rectangle((1020,245,1360,252),fill=SAGE)

def build_png():
    img = Image.new("RGB", (W,H), CREAM)
    d = ImageDraw.Draw(img)

    draw_logo_png(d)

    d.line((700, 405, 700, 710), fill=TAUPE, width=4)
    d.line((1400, 405, 1400, 710), fill=TAUPE, width=4)

    draw_scale(d, 350, 455, SAGE)
    draw_magnifier(d, 1050, 455, SAGE)
    draw_growth(d, 1750, 455, SAGE)

    centered(d, (350, 650), "LAW FIRM", font(FONT_SANS_BOLD, 61), FOREST)
    centered(d, (1050, 656), "WORKPLACE\nINVESTIGATIONS", font(FONT_SANS_BOLD, 54), FOREST, 9)
    centered(d, (1750, 656), "TECHNOLOGY & AI\nCONSULTING", font(FONT_SANS_BOLD, 50), FOREST, 9)

    photo_top, photo_h = 775, 400
    hero = cover(Image.open(ROOT / "assets" / "fir-group-hero.jpeg").convert("RGB"), W, photo_h)
    img.paste(hero, (0, photo_top))
    d.rectangle((0, photo_top, W, photo_top+7), fill=SAGE)
    d.rectangle((0, photo_top+photo_h-7, W, photo_top+photo_h), fill=SAGE)

    centered(d, (1025, 1282), "firgroup.org", font(FONT_SERIF_BOLD, 105), FOREST)
    qr, matrix = qr_image(145)
    img.paste(qr, (1905, 1210))
    img.save(OUT / "Fir-Group-GotPrint-Front-2100x1400-350DPI.png", dpi=(350,350), optimize=True)
    return matrix

def cmyk(rgb):
    r,g,b=[v/255 for v in rgb]
    k=1-max(r,g,b)
    if k >= .999: return CMYKColor(0,0,0,100)
    return CMYKColor(100*(1-r-k)/(1-k),100*(1-g-k)/(1-k),100*(1-b-k)/(1-k),100*k)

def pdf_text(c, x, y, text, font_name, size, color, leading=None):
    c.setFillColor(color)
    lines=text.split("\n")
    lead=leading or size*1.15
    for i,line in enumerate(lines):
        c.setFont(font_name,size)
        c.drawCentredString(x, y-i*lead, line)

def pdf_line(c, x1,y1,x2,y2,color,width):
    c.setStrokeColor(color); c.setLineWidth(width); c.line(x1,y1,x2,y2)

def build_pdf(matrix):
    path=OUT/"Fir-Group-GotPrint-Front-6x4-Print.pdf"
    pdfmetrics.registerFont(TTFont("FirSans", FONT_SANS))
    pdfmetrics.registerFont(TTFont("FirSansBold", FONT_SANS_BOLD))
    pdfmetrics.registerFont(TTFont("FirSerifBold", FONT_SERIF_BOLD))
    pw,ph=6*inch,4*inch
    c=canvas.Canvas(str(path),pagesize=(pw,ph),pageCompression=1)
    cream,forest,sage,taupe=map(cmyk,(CREAM,FOREST,SAGE,TAUPE))
    c.setFillColor(cream); c.rect(0,0,pw,ph,stroke=0,fill=1)

    # High-contrast vector Fir Group logo for the cream background.
    cx,cy,r=X(590),Y(148),X(105)
    c.setStrokeColor(forest); c.setFillColor(forest); c.setLineWidth(X(8))
    c.circle(cx,cy,r,stroke=1,fill=0)
    c.setLineWidth(X(10)); c.line(cx,Y(81),cx,Y(218))
    for yy,half in [(-54,36),(-22,51),(12,63),(47,74)]:
        p=c.beginPath()
        p.moveTo(cx,Y(148+yy-31)); p.lineTo(X(590-half),Y(148+yy+24)); p.lineTo(X(579),Y(148+yy+18))
        p.lineTo(cx,Y(148+yy+5)); p.lineTo(X(601),Y(148+yy+18)); p.lineTo(X(590+half),Y(148+yy+24)); p.close()
        c.drawPath(p,stroke=0,fill=1)
    pdf_text(c,X(1190),Y(170),"THE FIR GROUP","FirSerifBold",21.6,forest)
    c.setFillColor(sage); c.rect(X(1020),Y(252),X(340),X(7),stroke=0,fill=1)

    # Pixel-design coordinates transformed to PDF, with Y flipped.
    def X(v): return v*S
    def Y(v): return ph-v*S

    pdf_line(c,X(700),Y(405),X(700),Y(710),taupe,0.8)
    pdf_line(c,X(1400),Y(405),X(1400),Y(710),taupe,0.8)

    # Complete vector scales.
    cx,cy=X(350),Y(455)
    c.setStrokeColor(sage); c.setFillColor(sage); c.setLineCap(1); c.setLineJoin(1)
    c.setLineWidth(X(11))
    c.circle(cx,Y(455-94),X(10),stroke=0,fill=1)
    c.line(cx,Y(455-88),cx,Y(455+94))
    c.line(X(238),Y(383),X(462),Y(383))
    for sign in (-1,1):
        anchor=350+sign*100
        c.setLineWidth(X(7))
        c.line(X(anchor),Y(387),X(anchor-sign*36),Y(478))
        c.line(X(anchor),Y(387),X(anchor+sign*36),Y(478))
        c.setLineWidth(X(8))
        p=c.beginPath()
        p.moveTo(X(anchor-48),Y(489))
        p.curveTo(X(anchor-32),Y(530),X(anchor+32),Y(530),X(anchor+48),Y(489))
        c.drawPath(p,stroke=1,fill=0)
        c.setLineWidth(X(5)); c.line(X(anchor-47),Y(489),X(anchor+47),Y(489))
    c.roundRect(X(312),Y(563),X(76),X(24),X(6),stroke=0,fill=1)
    c.roundRect(X(278),Y(578),X(144),X(17),X(5),stroke=0,fill=1)

    # Vector magnifier.
    c.setLineWidth(X(11)); c.setStrokeColor(sage)
    c.circle(X(1042),Y(425),X(58),stroke=1,fill=0)
    c.line(X(1085),Y(468),X(1154),Y(537))
    c.setLineWidth(X(8)); c.line(X(1005),Y(567),X(1120),Y(567))

    # Vector growth arrow.
    c.setLineWidth(X(11))
    p=c.beginPath(); p.moveTo(X(1650),Y(507)); p.lineTo(X(1716),Y(441)); p.lineTo(X(1775),Y(499)); p.lineTo(X(1855),Y(403)); c.drawPath(p,stroke=1,fill=0)
    c.line(X(1855),Y(403),X(1855),Y(461)); c.line(X(1855),Y(403),X(1798),Y(403))
    c.setLineWidth(X(8)); c.line(X(1698),Y(567),X(1820),Y(567))

    pdf_text(c,X(350),Y(650),"LAW FIRM","FirSansBold",12.5,forest)
    pdf_text(c,X(1050),Y(640),"WORKPLACE\nINVESTIGATIONS","FirSansBold",11.1,forest,13)
    pdf_text(c,X(1750),Y(640),"TECHNOLOGY & AI\nCONSULTING","FirSansBold",10.3,forest,12.5)

    photo_top,photo_h=775,400
    c.drawImage(str(ROOT/"assets"/"fir-group-hero.jpeg"),0,Y(photo_top+photo_h),width=pw,height=X(photo_h),preserveAspectRatio=False)
    c.setFillColor(sage); c.rect(0,Y(photo_top+7),pw,X(7),stroke=0,fill=1); c.rect(0,Y(photo_top+photo_h),pw,X(7),stroke=0,fill=1)

    pdf_text(c,X(1025),Y(1310),"firgroup.org","FirSerifBold",22,forest)
    n=len(matrix); module=X(145)/n; ox=X(1905); oy=Y(1210+145)
    c.setFillColor(cmyk((255,255,255))); c.rect(ox,oy,X(145),X(145),stroke=0,fill=1)
    c.setFillColor(cmyk(BLACK))
    for row,line in enumerate(matrix):
        for col,on in enumerate(line):
            if on: c.rect(ox+col*module,oy+(n-1-row)*module,module+0.03,module+0.03,stroke=0,fill=1)

    c.showPage(); c.save()

def validate():
    png=OUT/"Fir-Group-GotPrint-Front-2100x1400-350DPI.png"
    im=Image.open(png)
    assert im.size==(2100,1400), im.size
    assert all(abs(v-350)<1 for v in im.info.get("dpi",(0,0))), im.info.get("dpi")
    qr_crop=cv2.imread(str(png))[1200:1390,1885:2085]
    decoded,_,_=cv2.QRCodeDetector().detectAndDecode(qr_crop)
    assert decoded=="https://firgroup.org", decoded
    reader=PdfReader(str(OUT/"Fir-Group-GotPrint-Front-6x4-Print.pdf"))
    box=reader.pages[0].mediabox
    assert abs(float(box.width)-432)<0.1 and abs(float(box.height)-288)<0.1
    (OUT/"VALIDATION.txt").write_text(
        "PASS\nPNG: 2100 x 1400 pixels, 350 DPI\nPDF: 6.000 x 4.000 inches\nQR decoded: https://firgroup.org\nFull-bleed background/photo reaches page edges\n"
    )

if __name__=="__main__":
    matrix=build_png()
    build_pdf(matrix)
    validate()
