"""Generování odpovědi na email klienta."""
from datetime import datetime


def compose_reply(
    client_name: str,
    items: list[dict],
    total_without_vat: float,
    total_with_vat: float,
    sender_name: str = "Filip",
) -> str:
    """Vygeneruje formální odpověď na email klienta."""

    # Oslovení
    if client_name:
        greeting = f"Dobrý den, {client_name},"
    else:
        greeting = "Dobrý den,"

    # Tabulka položek
    items_text = ""
    for item in items:
        items_text += (
            f"  - {item['product_name']}: "
            f"{item['quantity']} ks × {item['unit_price']:.2f} Kč = "
            f"{item['total_price']:.2f} Kč bez DPH\n"
        )

    # Sestavení emailu
    reply = f"""{greeting}

děkuji za Váš zájem. Níže zasílám cenovou kalkulaci dle Vašeho požadavku:

{items_text.rstrip()}

Celkem bez DPH: {total_without_vat:,.2f} Kč
Celkem s DPH (21 %): {total_with_vat:,.2f} Kč

Ceny jsou uvedeny bez DPH. V příloze zasílám podrobný produktový list s kalkulací.

V případě jakýchkoliv dotazů se neváhejte obrátit.

S pozdravem
{sender_name}
TWIN Production s.r.o."""

    return reply
