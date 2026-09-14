from pydantic import BaseModel, ConfigDict, Field


class ContractChangeOutput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    sections_changed: list[str] = Field(
        description="Cláusulas o secciones afectadas por la adenda."
    )

    topics_touched: list[str] = Field(
        description="Temas legales o contractuales afectados."
    )

    summary_of_the_change: str = Field(
        description="Resumen preciso de los cambios introducidos por la adenda."
    )