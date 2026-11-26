import os
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

load_dotenv()


def _get_port(default: int = 8000) -> int:
    """Obtiene el puerto desde la variable de entorno PORT o usa el valor por defecto."""
    raw_port = os.getenv("PORT", "").strip()
    if not raw_port:
        return default
    try:
        return int(raw_port)
    except ValueError:
        return default


PORT = _get_port(8000)

app = FastAPI(
    title="Eq. 01 · Product Manager API",
    description=(
        "API de la Estación 01 (Product Manager) para Dirección de Operaciones. "
        "Genera planes de producción estructurados a partir de solicitudes."
    ),
    version="0.1.0",
)


class HealthResponse(BaseModel):
    """Respuesta del endpoint de estado del servicio."""

    status: str = Field(..., description="Estado operativo del servicio.", examples=["ok"])
    station: str = Field(
        ...,
        description="Identificador de la estación.",
        examples=["01-product-manager"],
    )


class ProductionPlanRequest(BaseModel):
    """Solicitud de planificación de producción."""

    product_name: str = Field(
        ...,
        min_length=1,
        description="Nombre del producto a fabricar.",
        examples=["Silla ergonómica modelo A"],
    )
    quantity: int = Field(
        ...,
        gt=0,
        description="Cantidad de unidades solicitadas.",
        examples=[150],
    )
    deadline_days: int = Field(
        ...,
        gt=0,
        description="Plazo máximo de entrega en días.",
        examples=[10],
    )
    notes: str | None = Field(
        default=None,
        description="Notas u observaciones opcionales para la planificación.",
        examples=["Priorizar acabado mate y empaque reforzado"],
    )


class PlanPhase(BaseModel):
    """Fase dentro del plan de producción con sus tareas estimadas."""

    phase_number: int = Field(..., ge=1, description="Número de orden de la fase.")
    name: str = Field(..., description="Nombre descriptivo de la fase.")
    estimated_days: float = Field(..., gt=0, description="Duración estimada en días.")
    tasks: list[str] = Field(..., min_length=1, description="Tareas estimadas de la fase.")


class ProductionPlanResponse(BaseModel):
    """Plan de producción estructurado devuelto por la estación."""

    plan_id: str = Field(
        ...,
        description="Identificador único del plan generado.",
        examples=["PLAN-A1B2C3D4"],
    )
    product_name: str = Field(..., description="Nombre del producto planificado.")
    quantity: int = Field(..., gt=0, description="Cantidad total planificada.")
    deadline_days: int = Field(..., gt=0, description="Plazo máximo en días.")
    phases: list[PlanPhase] = Field(
        ...,
        description="Desglose de fases y tareas estimadas.",
    )
    notes: str | None = Field(
        default=None,
        description="Notas u observaciones asociadas a la solicitud.",
    )
    status: str = Field(
        default="planned",
        description="Estado actual del plan de producción.",
        examples=["planned"],
    )


@app.get("/health", response_model=HealthResponse, tags=["Salud"])
def get_health() -> HealthResponse:
    """Verifica que el servicio de la estación esté activo."""
    return HealthResponse(status="ok", station="01-product-manager")


@app.post("/api/v1/pm/plan", response_model=ProductionPlanResponse, tags=["Product Manager"])
def create_production_plan(request: ProductionPlanRequest) -> ProductionPlanResponse:
    """Genera un plan de producción estructurado de prueba para la solicitud dada."""
    plan_id = f"PLAN-{uuid4().hex[:8].upper()}"

    prep_days = max(1.0, round(request.deadline_days * 0.2, 1))
    exec_days = max(1.0, round(request.deadline_days * 0.6, 1))
    qc_days = max(0.5, round(request.deadline_days - prep_days - exec_days, 1))
    if qc_days <= 0:
        qc_days = 1.0

    phases = [
        PlanPhase(
            phase_number=1,
            name="Aprovisionamiento y preparación",
            estimated_days=prep_days,
            tasks=[
                f"Validar especificaciones de {request.product_name}",
                f"Reservar materia prima para {request.quantity} unidades",
                "Asignar línea y recursos iniciales",
            ],
        ),
        PlanPhase(
            phase_number=2,
            name="Ejecución de producción",
            estimated_days=exec_days,
            tasks=[
                f"Configurar maquinaria para lote de {request.quantity} unidades",
                "Ejecutar manufactura y ensamblaje por lotes",
                "Registrar avance diario de estación",
            ],
        ),
        PlanPhase(
            phase_number=3,
            name="Control de calidad y despacho",
            estimated_days=qc_days,
            tasks=[
                "Inspeccionar muestra representativa del lote",
                "Empacar producto terminado y generar orden de salida",
            ],
        ),
    ]

    return ProductionPlanResponse(
        plan_id=plan_id,
        product_name=request.product_name,
        quantity=request.quantity,
        deadline_days=request.deadline_days,
        phases=phases,
        notes=request.notes,
        status="planned",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
