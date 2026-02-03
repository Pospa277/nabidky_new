"""Admin routes - správa produktů a ceníku."""
import os
import uuid
from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, PriceTier

router = APIRouter(prefix="/admin", tags=["admin"])
_TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
templates = Jinja2Templates(directory=_TEMPLATE_DIR)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "uploads")


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """Admin dashboard - přehled produktů."""
    products = db.query(Product).filter(Product.active == True).order_by(Product.name).all()
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "products": products,
    })


@router.get("/products/new", response_class=HTMLResponse)
async def new_product_form(request: Request):
    """Formulář pro nový produkt."""
    return templates.TemplateResponse("admin/product_form.html", {
        "request": request,
        "product": None,
        "price_tiers": [],
    })


@router.post("/products/new")
async def create_product(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    category: str = Form(""),
    image_url: str = Form(""),
    shipping_cost: float = Form(0.0),
    image_file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    """Vytvoření nového produktu."""
    product = Product(
        name=name,
        description=description,
        category=category,
        image_url=image_url,
        shipping_cost=shipping_cost,
    )

    # Upload obrázku
    if image_file and image_file.filename:
        ext = os.path.splitext(image_file.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filepath = os.path.join(UPLOAD_DIR, filename)
        content = await image_file.read()
        with open(filepath, "wb") as f:
            f.write(content)
        product.image_local = filename

    db.add(product)
    db.commit()
    db.refresh(product)

    return RedirectResponse(url=f"/admin/products/{product.id}/edit", status_code=303)


@router.get("/products/{product_id}/edit", response_class=HTMLResponse)
async def edit_product_form(request: Request, product_id: int, db: Session = Depends(get_db)):
    """Formulář pro editaci produktu."""
    product = db.query(Product).get(product_id)
    if not product:
        return RedirectResponse(url="/admin/")
    return templates.TemplateResponse("admin/product_form.html", {
        "request": request,
        "product": product,
        "price_tiers": product.price_tiers,
    })


@router.post("/products/{product_id}/edit")
async def update_product(
    request: Request,
    product_id: int,
    name: str = Form(...),
    description: str = Form(""),
    category: str = Form(""),
    image_url: str = Form(""),
    shipping_cost: float = Form(0.0),
    image_file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    """Aktualizace produktu."""
    product = db.query(Product).get(product_id)
    if not product:
        return RedirectResponse(url="/admin/")

    product.name = name
    product.description = description
    product.category = category
    product.image_url = image_url
    product.shipping_cost = shipping_cost

    if image_file and image_file.filename:
        ext = os.path.splitext(image_file.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filepath = os.path.join(UPLOAD_DIR, filename)
        content = await image_file.read()
        with open(filepath, "wb") as f:
            f.write(content)
        product.image_local = filename

    db.commit()
    return RedirectResponse(url=f"/admin/products/{product_id}/edit", status_code=303)


@router.post("/products/{product_id}/delete")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Smazání produktu (soft delete)."""
    product = db.query(Product).get(product_id)
    if product:
        product.active = False
        db.commit()
    return RedirectResponse(url="/admin/", status_code=303)


# === Cenové stupně ===

@router.post("/products/{product_id}/tiers")
async def add_price_tier(
    product_id: int,
    min_quantity: int = Form(...),
    max_quantity: int = Form(None),
    price_per_unit: float = Form(...),
    db: Session = Depends(get_db),
):
    """Přidání cenového stupně."""
    tier = PriceTier(
        product_id=product_id,
        min_quantity=min_quantity,
        max_quantity=max_quantity,
        price_per_unit=price_per_unit,
    )
    db.add(tier)
    db.commit()
    return RedirectResponse(url=f"/admin/products/{product_id}/edit", status_code=303)


@router.post("/products/{product_id}/tiers/{tier_id}/delete")
async def delete_price_tier(product_id: int, tier_id: int, db: Session = Depends(get_db)):
    """Smazání cenového stupně."""
    tier = db.query(PriceTier).get(tier_id)
    if tier:
        db.delete(tier)
        db.commit()
    return RedirectResponse(url=f"/admin/products/{product_id}/edit", status_code=303)
