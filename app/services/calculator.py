"""Kalkulace cen nabídky."""
from sqlalchemy.orm import Session
from app.models import Product


def calculate_item_price(product: Product, quantity: int) -> dict:
    """Vypočítá cenu pro produkt a množství."""
    unit_price = product.get_price_for_quantity(quantity)

    if unit_price is None:
        # Pokud není definován cenový stupeň, vezmeme nejbližší
        if product.price_tiers:
            # Seřazeno podle min_quantity
            tiers = sorted(product.price_tiers, key=lambda t: t.min_quantity)
            if quantity < tiers[0].min_quantity:
                unit_price = tiers[0].price_per_unit
            else:
                unit_price = tiers[-1].price_per_unit
        else:
            unit_price = 0.0

    total = round(unit_price * quantity, 2)
    shipping = product.shipping_cost or 0.0

    return {
        "product_id": product.id,
        "product_name": product.name,
        "quantity": quantity,
        "unit_price": unit_price,
        "total_price": total,
        "shipping_cost": shipping,
        "total_with_shipping": round(total + shipping, 2),
    }


def calculate_quote(items: list[dict], db: Session) -> dict:
    """Vypočítá celou nabídku.

    items: [{"product_id": int, "quantity": int}, ...]
    """
    calculated_items = []
    total_without_vat = 0.0
    total_shipping = 0.0

    for item in items:
        product = db.query(Product).get(item["product_id"])
        if not product:
            continue

        calc = calculate_item_price(product, item["quantity"])
        calculated_items.append(calc)
        total_without_vat += calc["total_price"]
        total_shipping += calc["shipping_cost"]

    vat_rate = 0.21
    vat_amount = round(total_without_vat * vat_rate, 2)
    total_with_vat = round(total_without_vat + vat_amount, 2)

    return {
        "items": calculated_items,
        "subtotal": round(total_without_vat, 2),
        "shipping": round(total_shipping, 2),
        "vat_rate": vat_rate,
        "vat_amount": vat_amount,
        "total_without_vat": round(total_without_vat + total_shipping, 2),
        "total_with_vat": round(total_with_vat + total_shipping, 2),
    }
