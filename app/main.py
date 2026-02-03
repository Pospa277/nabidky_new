"""Hlavní FastAPI aplikace - Nabídkový generátor TWIN Production."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import init_db
from app.routes import quotes, admin

app = FastAPI(title="TWIN Production - Nabídkový generátor")

# Statické soubory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Routy
app.include_router(quotes.router)
app.include_router(admin.router)


@app.on_event("startup")
def startup():
    """Inicializace databáze při startu."""
    init_db()
    seed_sample_data()


def seed_sample_data():
    """Naplnění ukázkovými daty, pokud je databáze prázdná."""
    from app.database import SessionLocal
    from app.models import Product, PriceTier

    db = SessionLocal()
    try:
        if db.query(Product).count() > 0:
            return

        products = [
            {
                "name": "Náplasti Pocket Box",
                "description": "Reklamní náplasti v praktické krabičce s potiskem loga. Krabička obsahuje 10 ks náplastí.",
                "category": "Osobní péče",
                "image_url": "https://images.unsplash.com/photo-1583947215259-38e31be8751f?w=400&h=300&fit=crop",
                "shipping_cost": 0,
                "tiers": [
                    (100, 299, 38.00),
                    (300, 499, 34.00),
                    (500, 999, 30.00),
                    (1000, None, 26.00),
                ],
            },
            {
                "name": "Kondom Fólie 50",
                "description": "Reklamní kondom v potisku fólii s vlastním grafickým návrhem. Ideální propagační předmět.",
                "category": "Osobní péče",
                "image_url": "https://images.unsplash.com/photo-1584362917165-526a968579e8?w=400&h=300&fit=crop",
                "shipping_cost": 0,
                "tiers": [
                    (100, 299, 36.00),
                    (300, 499, 32.00),
                    (500, 999, 28.00),
                    (1000, None, 25.00),
                ],
            },
            {
                "name": "Antibakteriální gel 50ml",
                "description": "Antibakteriální gel v lahvičce s vlastním potiskem. Obsahuje 70% alkoholu.",
                "category": "Hygiena",
                "image_url": "https://images.unsplash.com/photo-1584483766114-2cea6facdf57?w=400&h=300&fit=crop",
                "shipping_cost": 150,
                "tiers": [
                    (50, 199, 45.00),
                    (200, 499, 39.00),
                    (500, 999, 34.00),
                    (1000, None, 29.00),
                ],
            },
            {
                "name": "Vlhčené ubrousky - box",
                "description": "Plastový zásobník s vlhčenými ubrousky. Velký prostor pro reklamní grafiku.",
                "category": "Hygiena",
                "image_url": "https://images.unsplash.com/photo-1585386959984-a4155224a1ad?w=400&h=300&fit=crop",
                "shipping_cost": 200,
                "tiers": [
                    (100, 299, 55.00),
                    (300, 499, 48.00),
                    (500, 999, 42.00),
                    (1000, None, 36.00),
                ],
            },
            {
                "name": "Papírové kapesníky - balení",
                "description": "Reklamní papírové kapesníky v balení s potiskem. 10 ks kapesníků v balení.",
                "category": "Hygiena",
                "image_url": "https://images.unsplash.com/photo-1583947581924-860bda6a26df?w=400&h=300&fit=crop",
                "shipping_cost": 0,
                "tiers": [
                    (200, 499, 12.00),
                    (500, 999, 9.50),
                    (1000, 4999, 7.50),
                    (5000, None, 6.00),
                ],
            },
        ]

        for pdata in products:
            product = Product(
                name=pdata["name"],
                description=pdata["description"],
                category=pdata["category"],
                image_url=pdata["image_url"],
                shipping_cost=pdata["shipping_cost"],
            )
            db.add(product)
            db.flush()

            for min_q, max_q, price in pdata["tiers"]:
                tier = PriceTier(
                    product_id=product.id,
                    min_quantity=min_q,
                    max_quantity=max_q,
                    price_per_unit=price,
                )
                db.add(tier)

        db.commit()
    finally:
        db.close()
