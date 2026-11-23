from pydantic import BaseModel, Field


class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    amount: float


class Invoice(BaseModel):
    """Target schema. Fields the document does not state are null, never guessed."""

    vendor: str | None = Field(None, description="Seller / issuer name")
    invoice_number: str | None = None
    invoice_date: str | None = Field(None, description="YYYY-MM-DD")
    currency: str | None = Field(None, description="ISO 4217 code, e.g. USD, INR")
    line_items: list[LineItem] = Field(default_factory=list)
    subtotal: float | None = None
    tax: float | None = None
    total: float | None = None
    notes: list[str] = Field(
        default_factory=list,
        description="Ambiguities, missing fields or assumptions made during extraction",
    )


OUTPUT_FORMAT = {"type": "json_schema", "schema": Invoice.model_json_schema()}
