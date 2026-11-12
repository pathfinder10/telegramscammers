#!/usr/bin/env python3
"""Build a PDF of the 70-channel watcher-bot target list."""
import json, os
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT

BASE = os.path.expanduser("~/workspace/telegramscammers-site")
data = json.load(open(os.path.join(BASE, "channel-list-for-bot.json")))
channels = data["channels"]

OUT = os.path.expanduser("~/workspace/your_files/telegram-funnel-channel-list.pdf")

RED = HexColor("#B22222"); DARK = HexColor("#111111"); GRAY = HexColor("#555555")
GOLD = HexColor("#C9A227")

title_style = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=20, textColor=RED, spaceAfter=6)
sub_style = ParagraphStyle("sub", fontName="Helvetica", fontSize=10, textColor=GRAY, spaceAfter=12)
cell = ParagraphStyle("cell", fontName="Helvetica", fontSize=8, leading=10, textColor=DARK)
cell_b = ParagraphStyle("cellb", parent=cell, fontName="Helvetica-Bold")
hdr = ParagraphStyle("hdr", parent=cell, fontName="Helvetica-Bold", textColor="white", fontSize=8)
foot = ParagraphStyle("foot", fontName="Helvetica", fontSize=9, textColor=GRAY, spaceBefore=12)

doc = SimpleDocTemplate(OUT, pagesize=LETTER, leftMargin=0.5*inch, rightMargin=0.5*inch,
                        topMargin=0.6*inch, bottomMargin=0.6*inch,
                        title="Telegram Funnel Channel List", author="telegramscammers.com")
story = [Paragraph("TELEGRAM FUNNEL CHANNEL LIST", title_style),
         Paragraph("70 channels tracked by telegramscammers.com — prepared for the watcher-bot aggregate. "
                   f"{sum(1 for c in channels if c['type']=='public')} public, "
                   f"{sum(1 for c in channels if c['type']=='private_invite')} private invites. "
                   "Flagged for investigation — not a finding of fraud.", sub_style)]

rows = [[Paragraph("<b>#</b>", hdr), Paragraph("<b>Channel</b>", hdr),
         Paragraph("<b>Type</b>", hdr), Paragraph("<b>AfterHour sources</b>", hdr)]]
for i, c in enumerate(channels, 1):
    label = ("t.me/" + c["handle"]) if c["type"] == "public" else "private invite"
    rows.append([Paragraph(str(i), cell),
                 Paragraph(label, cell_b),
                 Paragraph(c["type"].replace("_", " "), cell),
                 Paragraph(", ".join(c["afterhour_sources"]), cell)])

t = Table(rows, colWidths=[0.4*inch, 2.2*inch, 1.1*inch, 3.5*inch], repeatRows=1)
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), RED),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), ["white", HexColor("#F5F5F5")]),
    ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
]))
story += [t, Paragraph("Source: telegramscammers.com open data — full database at telegramscammers.com/database", foot)]
doc.build(story)
print("wrote", OUT)
