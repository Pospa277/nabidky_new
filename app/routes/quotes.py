"""Routes pro nabídky - hlavní workflow."""
import json
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, Quote, QuoteItem
from app.services.email_parser import parse_client_email
from app.services.calculator import calculate_quote
from app.services.email_composer import compose_reply
from app.services.pdf_generator import generate_quote_pdf

router = APIRouter(tags=["quotes"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Hlavní stránka - vložení emailu."""
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/parse-email", response_class=HTMLResponse)
async def parse_email(request: Request, email_text: str = Form(...), db: Session = Depends(get_db)):
    """Parsování emailu a zobrazení formuláře s předvyplněnými údaji."""
    parsed = parse_client_email(email_text)

    # Hledání produktů v databázi podle klíčových slov
    products = db.query(Product).filter(Product.active == True).all()
    matched_products = []

    for product in products:
        product_name_lower = product.name.lower()
        for kw in parsed.products:
            if kw["keyword"] in product_name_lower:
                matched_products.append(product)
                break

    # Pokud nic nebylo nalezeno, nabídni všechny produkty
    all_products = products

    return templates.TemplateResponse("quote_form.html", {
        "request": request,
        "parsed": parsed,
        "matched_products": matched_products,
        "all_products": all_products,
        "quantities": parsed.quantities,
        "email_text": email_text,
    })


@router.post("/generate-quote", response_class=HTMLResponse)
async def generate_quote(request: Request, db: Session = Depends(get_db)):
    """Generování nabídky z formuláře."""
    form_data = await request.form()

    client_name = form_data.get("client_name", "")
    email_text = form_data.get("email_text", "")

    # Zpracování položek z formuláře
    items = []
    i = 0
    while f"product_id_{i}" in form_data:
        product_id = form_data.get(f"product_id_{i}")
        quantity = form_data.get(f"quantity_{i}")
        if product_id and quantity:
            try:
                items.append({
                    "product_id": int(product_id),
                    "quantity": int(quantity),
                })
            except (ValueError, TypeError):
                pass
        i += 1

    if not items:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "Nebyla vybrána žádná položka.",
        })

    # Kalkulace
    calculation = calculate_quote(items, db)

    # Vytvoření nabídky v DB
    quote = Quote(
        client_name=client_name,
        original_email=email_text,
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)

    # Přidání položek
    for calc_item in calculation["items"]:
        quote_item = QuoteItem(
            quote_id=quote.id,
            product_id=calc_item["product_id"],
            product_name=calc_item["product_name"],
            quantity=calc_item["quantity"],
            unit_price=calc_item["unit_price"],
            total_price=calc_item["total_price"],
        )
        db.add(quote_item)

    # Generování emailové odpovědi
    email_reply = compose_reply(
        client_name=client_name,
        items=calculation["items"],
        total_without_vat=calculation["total_without_vat"],
        total_with_vat=calculation["total_with_vat"],
    )
    quote.email_reply = email_reply

    # Generování PDF
    product_images = {}
    product_descriptions = {}
    for calc_item in calculation["items"]:
        product = db.query(Product).get(calc_item["product_id"])
        if product:
            product_images[product.id] = product.get_image()
            product_descriptions[product.id] = product.description

    pdf_path = generate_quote_pdf(
        quote_id=quote.id,
        client_name=client_name,
        items=calculation["items"],
        total_without_vat=calculation["total_without_vat"],
        total_with_vat=calculation["total_with_vat"],
        vat_amount=calculation["vat_amount"],
        shipping=calculation["shipping"],
        product_images=product_images,
        product_descriptions=product_descriptions,
    )
    quote.pdf_path = pdf_path

    db.commit()

    return templates.TemplateResponse("quote_result.html", {
        "request": request,
        "quote": quote,
        "calc_items": calculation["items"],
        "calc_subtotal": calculation["subtotal"],
        "calc_shipping": calculation["shipping"],
        "calc_total_without_vat": calculation["total_without_vat"],
        "calc_vat_amount": calculation["vat_amount"],
        "calc_total_with_vat": calculation["total_with_vat"],
        "email_reply": email_reply,
        "pdf_path": pdf_path,
    })


@router.get("/download-pdf/{quote_id}")
async def download_pdf(quote_id: int, db: Session = Depends(get_db)):
    """Stažení PDF nabídky."""
    quote = db.query(Quote).get(quote_id)
    if not quote or not quote.pdf_path:
        return RedirectResponse(url="/")

    import os
    filename = os.path.basename(quote.pdf_path)
    return FileResponse(
        path=quote.pdf_path,
        filename=filename,
        media_type="application/pdf",
    )


@router.get("/history", response_class=HTMLResponse)
async def quote_history(request: Request, db: Session = Depends(get_db)):
    """Historie nabídek."""
    quotes = db.query(Quote).order_by(Quote.created_at.desc()).limit(50).all()
    return templates.TemplateResponse("history.html", {
        "request": request,
        "quotes": quotes,
    })
