"""Generování PDF nabídky."""
import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "pdf_templates")
OUTPUT_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")


def generate_quote_pdf(
    quote_id: int,
    client_name: str,
    items: list[dict],
    total_without_vat: float,
    total_with_vat: float,
    vat_amount: float,
    shipping: float = 0.0,
    product_images: dict | None = None,
    product_descriptions: dict | None = None,
) -> str:
    """Vygeneruje PDF nabídky a vrátí cestu k souboru."""

    if product_images is None:
        product_images = {}
    if product_descriptions is None:
        product_descriptions = {}

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("quote_template.html")

    # Příprava dat pro šablonu
    enriched_items = []
    for item in items:
        enriched = dict(item)
        pid = item.get("product_id", 0)
        enriched["image_url"] = product_images.get(pid, "")
        enriched["description"] = product_descriptions.get(pid, "")
        enriched_items.append(enriched)

    html_content = template.render(
        quote_id=quote_id,
        date=datetime.now().strftime("%d. %m. %Y"),
        client_name=client_name,
        items=enriched_items,
        total_without_vat=f"{total_without_vat:,.2f}".replace(",", " "),
        total_with_vat=f"{total_with_vat:,.2f}".replace(",", " "),
        vat_amount=f"{vat_amount:,.2f}".replace(",", " "),
        shipping=f"{shipping:,.2f}".replace(",", " "),
        year=datetime.now().year,
    )

    # Výstupní soubor
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f"nabidka_{quote_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    # Generování PDF
    html = HTML(string=html_content, base_url=BASE_DIR)
    html.write_pdf(filepath)

    return filepath
