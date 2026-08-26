from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from fastapi import HTTPException
from app.config.database import db


async def generar_reporte_stock_bajo_pdf() -> BytesIO: # Genera un reporte PDF de productos con stock bajo en todos los almacenes
    try:
        query = """
            SELECT 
                p.codigo AS codigo,
                p.nombre AS producto,
                a.nombre AS almacen,
                sa.cantidad_disponible AS stock_actual,
                p.stock_minimo AS stock_minimo,
                (p.stock_minimo - sa.cantidad_disponible) AS deficit,
                CASE 
                    WHEN sa.cantidad_disponible = 0 THEN 'CRÍTICO'
                    WHEN sa.cantidad_disponible < (p.stock_minimo * 0.5) THEN 'URGENTE'
                    ELSE 'BAJO'
                END AS estado
            FROM stock_almacen sa
            INNER JOIN productos p ON sa.fk_producto = p.id
            INNER JOIN almacenes a ON sa.fk_almacen = a.id
            WHERE sa.cantidad_disponible < p.stock_minimo
            AND p.activo = 1
            ORDER BY 
                CASE 
                    WHEN sa.cantidad_disponible = 0 THEN 1
                    WHEN sa.cantidad_disponible < (p.stock_minimo * 0.5) THEN 2
                    ELSE 3
                END,
                a.nombre,
                p.nombre
        """

        rows = await db.fetch_all(query=query)

        if not rows:
            raise HTTPException(
                status_code=404, detail="No se encontraron productos con stock bajo"
            )

        # Crear PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30,
        )

        elements = []
        styles = getSampleStyleSheet()

        #  ENCABEZADO
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#1a237e"),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )

        subtitle_style = ParagraphStyle(
            "CustomSubtitle",
            parent=styles["Normal"],
            fontSize=11,
            textColor=colors.black,
            alignment=TA_CENTER,
        )

        titulo = Paragraph("Reporte de Stock Bajo", title_style)
        elements.append(titulo)

        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
        fecha = Paragraph(f"Generado el: {fecha_actual}", subtitle_style)
        elements.append(fecha)
        elements.append(Spacer(1, 20))

        # RESUMEN 
        total_productos = len(rows)
        criticos = sum(1 for r in rows if r["estado"] == "CRÍTICO")
        urgentes = sum(1 for r in rows if r["estado"] == "URGENTE")
        bajos = sum(1 for r in rows if r["estado"] == "BAJO")

        resumen_data = [
            ["Estado", "Cantidad"],
            ["CRÍTICO (sin stock)", str(criticos)],
            ["URGENTE (< 50% mínimo)", str(urgentes)],
            ["BAJO (< stock mínimo)", str(bajos)],
            ["TOTAL", str(total_productos)],
        ]

        resumen_table = Table(resumen_data, colWidths=[3 * inch, 1.5 * inch])
        resumen_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e0e0e0")),
                ]
            )
        )

        elements.append(resumen_table)
        elements.append(Spacer(1, 30))

        # DETALLE
        detalle_titulo = Paragraph("Detalle de Productos", title_style)
        elements.append(detalle_titulo)
        elements.append(Spacer(1, 12))

        data = [
            [
                "Código",
                "Producto",
                "Almacén",
                "Stock Actual",
                "Mínimo",
                "Déficit",
                "Estado",
            ]
        ]

        for row in rows:
            data.append(
                [
                    str(row["codigo"]),
                    str(row["producto"]),
                    str(row["almacen"]),
                    str(row["stock_actual"]),
                    str(row["stock_minimo"]),
                    str(row["deficit"]),
                    str(row["estado"]),
                ]
            )

        table = Table(data, colWidths=[None] * len(data[0]))  

        table_style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]

        # Colorear columna de estado
        for i, row in enumerate(rows, start=1):
            if row["estado"] == "CRÍTICO":
                table_style.append(("BACKGROUND", (-1, i), (-1, i), colors.red))
                table_style.append(("TEXTCOLOR", (-1, i), (-1, i), colors.white))
            elif row["estado"] == "URGENTE":
                table_style.append(("BACKGROUND", (-1, i), (-1, i), colors.orange))
            else:
                table_style.append(("BACKGROUND", (-1, i), (-1, i), colors.yellow))

        table.setStyle(TableStyle(table_style))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return buffer

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al generar reporte PDF: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error al generar el reporte: {str(e)}"
        )


async def generar_reporte_inventario_general_pdf() -> BytesIO: # Genera un reporte PDF del inventario general 
    try:
        query = """
            SELECT 
                p.codigo AS codigo,
                p.nombre AS producto,
                c.nombre AS categoria,
                a.nombre AS almacen,
                sa.cantidad_disponible AS disponible,
                sa.cantidad_reservada AS reservada,
                (sa.cantidad_disponible + sa.cantidad_reservada) AS total,
                p.precio_venta AS precio,
                (sa.cantidad_disponible * p.precio_venta) AS valor_stock
            FROM stock_almacen sa
            INNER JOIN productos p ON sa.fk_producto = p.id
            INNER JOIN almacenes a ON sa.fk_almacen = a.id
            INNER JOIN categorias c ON p.fk_categoria = c.id
            WHERE p.activo = 1
            ORDER BY a.nombre, c.nombre, p.nombre
        """
        rows = await db.fetch_all(query=query)

        if not rows:
            raise HTTPException(
                status_code=404, detail="No se encontraron productos en el inventario"
            )

        # Crear PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30,
        )

        elements = []
        styles = getSampleStyleSheet()

        # Título
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#1a237e"),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )

        titulo = Paragraph("Reporte de Inventario General", title_style)
        elements.append(titulo)

        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
        fecha = Paragraph(
            f"Generado el: {fecha_actual}",
            ParagraphStyle(
                "subtitle", parent=styles["Normal"], fontSize=11, alignment=TA_LEFT
            ),
        )
        elements.append(fecha)
        elements.append(Spacer(1, 20))

        # Resumen
        valor_total = sum(float(r["valor_stock"]) for r in rows)

        resumen = Paragraph(
            f"<b>Valor total del inventario:</b> ${valor_total:,.2f}",
            styles["Normal"],
        )
        elements.append(resumen)
        elements.append(Spacer(1, 20))

        # Tabla
        data = [
            [
                "Código",
                "Producto",
                "Categoría",
                "Almacén",
                "Disponible",
                "Reservada",
                "Precio",
                "Valor",
            ]
        ]

        for row in rows:
            data.append(
                [
                    str(row["codigo"]),
                    str(row["producto"])[:20],
                    str(row["categoria"])[:15],
                    str(row["almacen"])[:15],
                    str(row["disponible"]),
                    str(row["reservada"]),
                    f"${float(row['precio']):,.2f}",
                    f"${float(row['valor_stock']):,.2f}",
                ]
            )

        table = Table(
            data,
            colWidths=[None] * len(data[0])
        )

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTSIZE", (0, 1), (-1, -1), 7),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.lightgrey],
                    ),
                ]
            )
        )

        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return buffer

    except Exception as e:
        print(f"Error al generar reporte: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error al generar el reporte: {str(e)}"
        )


async def generar_reporte_movimientos_pdf(
    fecha_inicio: str = None, fecha_fin: str = None
) -> BytesIO:       # Genera un reporte PDF de movimientos de inventario según fechas
    try:
        # Query general de movimientos
        query = """
            SELECT 
                mi.id,
                DATE_FORMAT(mi.fecha_movimiento, '%d/%m/%Y %H:%i') AS fecha,
                mi.tipo_movimiento,
                p.codigo AS codigo_producto,
                p.nombre AS producto,
                a.nombre AS almacen,
                u.nombre AS usuario,
                mi.cantidad,
                mi.cantidad_anterior,
                mi.cantidad_nueva,
                mi.motivo,
                prov.nombre AS proveedor
            FROM movimientos_inventario mi
            INNER JOIN productos p ON mi.fk_producto = p.id
            INNER JOIN almacenes a ON mi.fk_almacen = a.id
            INNER JOIN usuarios u ON mi.fk_usuario = u.id
            LEFT JOIN proveedores prov ON mi.fk_proveedor = prov.id
            WHERE 1=1
        """

        values = {}

        # Filtros opcionales solo por fecha
        if fecha_inicio:
            query += " AND DATE(mi.fecha_movimiento) >= :fecha_inicio"
            values["fecha_inicio"] = fecha_inicio

        if fecha_fin:
            query += " AND DATE(mi.fecha_movimiento) <= :fecha_fin"
            values["fecha_fin"] = fecha_fin

        query += " ORDER BY mi.fecha_movimiento DESC"

        rows = await db.fetch_all(query=query, values=values)

        if not rows:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron movimientos en el período especificado",
            )

        # Crear PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30,
        )

        elements = []
        styles = getSampleStyleSheet()

        # Estilos personalizados
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#1a237e"),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )

        subtitle_style = ParagraphStyle(
            "CustomSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.black,
            spaceAfter=12,
            alignment=TA_CENTER,
        )

        # Título
        titulo = Paragraph("Reporte General de Movimientos de Inventario", title_style)
        elements.append(titulo)

        # Información del reporte
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
        info_reporte = f"Generado el: {fecha_actual}"

        # Agregar período si se especificó
        if fecha_inicio and fecha_fin:
            info_reporte += f"<br/>Período: {fecha_inicio} al {fecha_fin}"
        elif fecha_inicio:
            info_reporte += f"<br/>Desde: {fecha_inicio}"
        elif fecha_fin:
            info_reporte += f"<br/>Hasta: {fecha_fin}"
        else:
            info_reporte += "<br/>Todos los movimientos registrados"

        fecha_parrafo = Paragraph(info_reporte, subtitle_style)
        elements.append(fecha_parrafo)
        elements.append(Spacer(1, 20))

        # Resumen estadístico
        total_movimientos = len(rows)
        entradas = sum(1 for r in rows if r["tipo_movimiento"] == "entrada")
        salidas = sum(1 for r in rows if r["tipo_movimiento"] == "salida")
        ajustes = sum(1 for r in rows if r["tipo_movimiento"] == "ajuste")
        devoluciones = sum(1 for r in rows if r["tipo_movimiento"] == "devolucion")

        # Contar almacenes únicos
        almacenes_unicos = len(set(r["almacen"] for r in rows))
        usuarios_unicos = len(set(r["usuario"] for r in rows))

        resumen_data = [
            ["Tipo de Movimiento", "Cantidad"],
            ["Entradas", str(entradas)],
            ["Salidas", str(salidas)],
            ["Ajustes", str(ajustes)],
            ["Devoluciones", str(devoluciones)],
            ["TOTAL MOVIMIENTOS", str(total_movimientos)],
            ["", ""],
            ["Almacenes involucrados", str(almacenes_unicos)],
            ["Usuarios que registraron", str(usuarios_unicos)],
        ]

        resumen_table = Table(resumen_data, colWidths=[3 * inch, 1.5 * inch])
        resumen_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, 5), colors.beige),
                    ("GRID", (0, 0), (-1, 5), 1, colors.black),
                    ("FONTNAME", (0, 5), (-1, 5), "Helvetica-Bold"),
                    ("BACKGROUND", (0, 5), (-1, 5), colors.HexColor("#e0e0e0")),
                    ("BACKGROUND", (0, 7), (-1, -1), colors.lightgrey),
                    ("GRID", (0, 7), (-1, -1), 1, colors.black),
                ]
            )
        )

        elements.append(resumen_table)
        elements.append(Spacer(1, 30))

        # Título de detalle
        detalle_titulo = Paragraph("Detalle de Movimientos", title_style)
        elements.append(detalle_titulo)
        elements.append(Spacer(1, 12))

        # Tabla de movimientos
        data = [
            [
                "Fecha",
                "Tipo",
                "Producto",
                "Almacén",
                "Cant.",
                "Stock Ant.",
                "Stock Nuevo",
                "Usuario",
            ]
        ]

        for row in rows:
            tipo = row["tipo_movimiento"].upper()

            data.append(
                [
                    str(row["fecha"]),
                    tipo[:3],  # Abreviado para ahorrar espacio
                    str(row["producto"])[:20],
                    str(row["almacen"])[:15],
                    str(row["cantidad"]),
                    str(row["cantidad_anterior"]),
                    str(row["cantidad_nueva"]),
                    str(row["usuario"])[:15],
                ]
            )

        # Crear tabla con anchos ajustados
        table = Table(
            data,
            colWidths=[
                1.0 * inch,  # Fecha
                0.5 * inch,  # Tipo
                1.8 * inch,  # Producto
                1.0 * inch,  # Almacén
                0.5 * inch,  # Cantidad
                0.7 * inch,  # Stock Ant
                0.8 * inch,  # Stock Nuevo
                1.0 * inch,  # Usuario
            ],
        )

        # Estilo base de la tabla
        table_style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 1), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]

        # Colorear según tipo de movimiento
        for i, row in enumerate(rows, start=1):
            tipo = row["tipo_movimiento"]
            if tipo == "entrada":
                table_style.append(("BACKGROUND", (1, i), (1, i), colors.lightgreen))
            elif tipo == "salida":
                table_style.append(("BACKGROUND", (1, i), (1, i), colors.lightcoral))
            elif tipo == "ajuste":
                table_style.append(("BACKGROUND", (1, i), (1, i), colors.lightyellow))
            elif tipo == "devolucion":
                table_style.append(("BACKGROUND", (1, i), (1, i), colors.lightblue))

        table.setStyle(TableStyle(table_style))
        elements.append(table)

        # Construir PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al generar reporte de movimientos: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error al generar el reporte: {str(e)}"
        )
