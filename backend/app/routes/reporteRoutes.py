from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.services.auth import require_auth
import app.services.reportes as service

router = APIRouter()


@router.get("/stock-bajo")
async def descargar_reporte_stock_bajo(usuario_actual=Depends(require_auth)):
    pdf_buffer = await service.generar_reporte_stock_bajo_pdf()

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=reporte_stock_bajo.pdf"},
    )


@router.get("/inventario-general")
async def descargar_reporte_inventario_general(usuario_actual=Depends(require_auth)):
    pdf_buffer = await service.generar_reporte_inventario_general_pdf()

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=reporte_inventario_general.pdf"
        },
    )


@router.get("/movimientos")
async def descargar_reporte_movimientos(
    fecha_inicio: str = None,
    fecha_fin: str = None,
    usuario_actual=Depends(require_auth),
):
    pdf_buffer = await service.generar_reporte_movimientos_pdf(
        fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )

    # Nombre del archivo según fechas
    if fecha_inicio and fecha_fin:
        filename = f"reporte_movimientos_{fecha_inicio}_al_{fecha_fin}.pdf"
    elif fecha_inicio:
        filename = f"reporte_movimientos_desde_{fecha_inicio}.pdf"
    elif fecha_fin:
        filename = f"reporte_movimientos_hasta_{fecha_fin}.pdf"
    else:
        filename = "reporte_movimientos_general.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
