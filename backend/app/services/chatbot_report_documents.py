"""Exportadores puros: el mismo dataset, sin consultas adicionales ni contenido LLM."""
from datetime import date
from io import BytesIO
import re
from xml.sax.saxutils import escape

MIME={"xlsx":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet","pdf":"application/pdf","docx":"application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
HEADERS=["Fecha","Curso","Estudiante","Estado","Período"]
KEYS=["fecha","curso","estudiante","estado","periodo"]

def clean(value):
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]","",str(value))

def display(value):
    if value is None:return "Sin datos disponibles"
    if isinstance(value,float):return f"{value:.2f}".replace(".",",")
    return clean(value)

def metrics_table(data):
    m=data["metrics"]
    rows=[["Indicador","Valor"],["Registros base del ámbito",m["registros"]],["Filas de este reporte",data["report_rows"]],
            ["Presentes",m["presentes"]],["Tardanzas",m["tardanzas"]],["Ausencias registradas",m["ausencias"]],
            ["Denominador de asistencia",m["denominador_asistencia"]],["Asistencia (%)",m["asistencia_pct"]],["Estados sin clasificar",m["sin_clasificar"]]]
    if data["comparison"]:rows.append(["Cambio del segundo período (puntos porcentuales)",data["comparison_delta_pp"]])
    return rows

def sections(data):
    if data.get("kind")=="ml_evaluation":
        cols=data["columns"]
        return [("Evaluación ML",[[label for _,label in cols]]+[[r[key] for key,_ in cols] for r in data["rows"]])]
    tables=[("Indicadores",metrics_table(data))]
    if data["comparison"]:
        tables.append(("Comparación",[["Período","Registros","Presentes","Tardanzas","Ausencias","Asistencia (%)"]]+[[r["periodo"],r["registros"],r["presentes"],r["tardanzas"],r["ausencias"],r["asistencia_pct"]] for r in data["comparison"]]))
    tables.append(("Registros",[HEADERS]+[[r[k] for k in KEYS] for r in data["rows"]]))
    if data["spec"]["report_type"]=="academico":
        tables.append(("Calificaciones disponibles",[["Curso","Estudiante","Evaluaciones calificadas","Promedio ponderado (0–20)"]]+[[r["curso"],r["estudiante"],r["evaluaciones"],r["promedio_ponderado"]] for r in data["grades"]]))
    return tables

def metadata(data,fingerprint):
    if data.get("kind")=="ml_evaluation":
        return [("Fuente",data["source"]),("Modalidad",data["mode_label"]),("Período",data["periods"][0]),("Generado",data["generated_at"]),("Huella del dataset",fingerprint)]
    return [("Fuente",data["source"]),("Modalidad","DATOS SINTÉTICOS DE PRUEBA" if data["synthetic"] else "Registros académicos autorizados"),
            ("Curso(s)","; ".join(c["nombre"] for c in data["courses"]) or "Sin cursos autorizados"),
            ("Período", " | ".join(data["periods"])),("Generado",data["generated_at"]),
            ("Filtro estudiante",str(data["spec"]["student_id"]) if data["spec"]["student_id"] else "Ámbito autorizado de la cuenta"),
            ("Huella del dataset",fingerprint)]

def excel(data,fingerprint):
    from openpyxl import Workbook
    from openpyxl.styles import Font,PatternFill,Alignment
    from openpyxl.chart import BarChart,Reference
    wb=Workbook();summary=wb.active;summary.title="Resumen"
    def append(ws,values):
        ws.append(values)
        for cell in ws[ws.max_row]:
            if isinstance(cell.value,str):
                cell.value=clean(cell.value);cell.data_type="s"
                # Incluso texto con espacios/control antes de =,+,-,@ permanece literal.
                if cell.value.lstrip(" \t\r\n\ufeff").startswith(("=","+","-","@")):cell.quotePrefix=True
            cell.alignment=Alignment(vertical="top",wrap_text=True)
    append(summary,["SENATI | Monitor IA Assistant"]);append(summary,[data["title"]])
    for label,value in metadata(data,fingerprint):append(summary,[label,value])
    append(summary,["Metodología",data["methodology"]])
    if data["spec"]["report_type"]=="academico":append(summary,["Calificaciones",data["grade_methodology"]])
    for title,table in sections(data):
        ws=wb.create_sheet({"Indicadores":"Indicadores","Comparación":"Comparacion","Registros":"Registros","Calificaciones disponibles":"Notas","Evaluación ML":"Evaluacion ML"}[title])
        for row in table:append(ws,row)
        if len(table)==1:append(ws,["Sin datos disponibles"])
        ws.freeze_panes="A2";ws.auto_filter.ref=ws.dimensions
        for cell in ws[1]:cell.fill=PatternFill("solid",fgColor="164A85");cell.font=Font(color="FFFFFF",bold=True)
        for row in ws.iter_rows(min_row=2):
            if row[0].row%2==0:
                for cell in row:cell.fill=PatternFill("solid",fgColor="EDF4FB")
    if data["chart"]:
        ws=wb.create_sheet("Grafico")
        append(ws,["Grupo", "Valor", "Unidad"])
        for item in data["chart"]:append(ws,[item["label"],item["value"],item["unit"]])
        chart=BarChart();chart.title="Distribución verificada";chart.y_axis.title=data["chart"][0]["unit"];chart.x_axis.title="Grupo"
        chart.add_data(Reference(ws,min_col=2,min_row=1,max_row=ws.max_row),titles_from_data=True)
        chart.set_categories(Reference(ws,min_col=1,min_row=2,max_row=ws.max_row));chart.height=10;chart.width=21;chart.display_blanks="gap"
        ws.add_chart(chart,"E2")
    for ws in wb:
        ws.sheet_view.showGridLines=False
        for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=24 if col[0].column<=1 else 43
        ws.oddHeader.center.text="Monitor IA Assistant | SENATI";ws.oddFooter.center.text="Confidencial · Página &P de &N"
        ws.print_options.horizontalCentered=True;ws.sheet_properties.pageSetUpPr.fitToPage=True
        ws.page_setup.orientation="landscape";ws.page_setup.fitToWidth=1;ws.page_setup.fitToHeight=0
    summary.column_dimensions["A"].width=27;summary.column_dimensions["B"].width=100
    summary.row_dimensions[summary.max_row].height=100
    summary["A1"].font=Font(bold=True,color="164A85",size=18);summary["A2"].font=Font(bold=True,size=14)
    output=BytesIO();wb.save(output);return output.getvalue()

def pdf(data,fingerprint):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4,landscape
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,LongTable,TableStyle,KeepTogether
    from reportlab.graphics.shapes import Drawing,Rect,String
    output=BytesIO();styles=getSampleStyleSheet()
    styles.add(ParagraphStyle("Cell",fontName="Helvetica",fontSize=8,leading=11,wordWrap="CJK"))
    styles["Title"].textColor=colors.HexColor("#164A85");styles["Title"].fontSize=20
    document=SimpleDocTemplate(output,pagesize=landscape(A4),rightMargin=32,leftMargin=32,topMargin=40,bottomMargin=35,title=data["title"],author="Monitor IA Assistant")
    def para(value):return Paragraph(escape(format(value,".6f").rstrip("0").rstrip(".") if data.get("kind")=="ml_evaluation" and isinstance(value,float) else display(value)),styles["Cell"])
    flow=[Paragraph("SENATI | Monitor IA Assistant",styles["Heading2"]),Paragraph(escape(data["title"]),styles["Title"])]
    for label,value in metadata(data,fingerprint):flow.append(para(label+": "+str(value)))
    flow.append(Spacer(1,12))
    for title,table in sections(data):
        flow.append(Paragraph(title,styles["Heading2"]))
        if len(table)==1:flow.extend([para("Sin datos disponibles"),Spacer(1,8)]);continue
        widths=[document.width/len(table[0])]*len(table[0])
        grid=LongTable([[para(c) for c in row] for row in table],colWidths=widths,repeatRows=1,hAlign="LEFT")
        grid.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#DCEBFA")),("GRID",(0,0),(-1,-1),.35,colors.HexColor("#CAD8E6")),("VALIGN",(0,0),(-1,-1),"TOP"),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F2F6FB")]),("LEFTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
        flow.extend([grid,Spacer(1,12)])
    chart=data["chart"]
    if chart and len(chart)<=12:
        drawing=Drawing(document.width,155);values=[item["value"] for item in chart if item["value"] is not None]
        maximum=max(values or [1]) or 1;step=document.width/len(chart)
        for index,item in enumerate(chart):
            x=index*step+15;value=item["value"]
            if value is not None:
                height=90*value/maximum;drawing.add(Rect(x,35,max(10,step-28),height,fillColor=colors.HexColor("#2768AF"),strokeWidth=0));drawing.add(String(x,40+height,display(value),fontSize=9))
            else:drawing.add(String(x,55,"Sin datos",fontSize=9))
            drawing.add(String(x,18,clean(item["label"])[:32],fontSize=7))
        flow.extend([Paragraph("Distribución verificada ("+escape(chart[0]["unit"])+")",styles["Heading2"]),drawing])
    elif not data["report_rows"]:flow.append(para("Sin datos disponibles"))
    flow.extend([Paragraph("Aclaraciones metodológicas",styles["Heading2"]),para(data["methodology"])])
    if data["spec"]["report_type"]=="academico":flow.append(para(data["grade_methodology"]))
    def page(canvas,doc):
        canvas.setFillColor(colors.HexColor("#164A85"));canvas.setFont("Helvetica",8)
        canvas.drawString(32,landscape(A4)[1]-22,"MONITOR IA ASSISTANT · REPORTE ACADÉMICO")
        canvas.drawString(32,18,"Confidencial · Uso académico autorizado");canvas.drawRightString(landscape(A4)[0]-32,18,f"Página {doc.page}")
    document.build(flow,onFirstPage=page,onLaterPages=page);return output.getvalue()

def word(data,fingerprint):
    from docx import Document
    from docx.shared import Inches,Pt,RGBColor
    from docx.oxml import OxmlElement
    document=Document();section=document.sections[0]
    section.top_margin=Inches(.7);section.bottom_margin=Inches(.7);section.left_margin=Inches(.65);section.right_margin=Inches(.65)
    normal=document.styles["Normal"];normal.font.name="Calibri";normal.font.size=Pt(10)
    section.header.paragraphs[0].text="SENATI | Monitor IA Assistant"
    section.header.paragraphs[0].runs[0].font.color.rgb=RGBColor.from_string("164A85")
    section.footer.paragraphs[0].text="Confidencial · Uso académico autorizado · Sin datos emocionales"
    document.add_heading(data["title"],0)
    for label,value in metadata(data,fingerprint):
        paragraph=document.add_paragraph();paragraph.add_run(label+": ").bold=True;paragraph.add_run(clean(value))
    for title,table in sections(data):
        document.add_heading(title,1)
        if len(table)==1:document.add_paragraph("Sin datos disponibles");continue
        grid=document.add_table(rows=1,cols=len(table[0]));grid.style="Light Shading Accent 1"
        header=OxmlElement("w:tblHeader");grid.rows[0]._tr.get_or_add_trPr().append(header)
        for cell,value in zip(grid.rows[0].cells,table[0]):cell.text=display(value)
        for row in table[1:]:
            for cell,value in zip(grid.add_row().cells,row):cell.text=format(value,".6f").rstrip("0").rstrip(".") if data.get("kind")=="ml_evaluation" and isinstance(value,float) else display(value)
    document.add_heading("Aclaraciones metodológicas",1);document.add_paragraph(data["methodology"])
    if data["spec"]["report_type"]=="academico":document.add_paragraph(data["grade_methodology"])
    output=BytesIO();document.save(output);return output.getvalue()

def render(data,fmt,fingerprint):
    return {"xlsx":excel,"pdf":pdf,"docx":word}[fmt](data,fingerprint)
