"""Parsování emailu od klienta."""
import re
from dataclasses import dataclass, field


@dataclass
class ParsedEmail:
    """Výsledek parsování emailu."""
    client_name: str = ""
    greeting: str = ""
    products: list[dict] = field(default_factory=list)
    quantities: list[int] = field(default_factory=list)
    print_info: str = ""
    urls: list[str] = field(default_factory=list)
    raw_text: str = ""


def parse_client_email(email_text: str) -> ParsedEmail:
    """Parsuje email od klienta a extrahuje klíčové informace."""
    result = ParsedEmail(raw_text=email_text)

    # Extrakce jména odesílatele (typicky na konci emailu)
    name_patterns = [
        r'(?:S pozdravem|Děkuji|Díky|S úctou|Hezký den).*?\n\s*([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+(?:\s+[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)?)',
        r'\n\s*([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)\s*$',
    ]
    for pattern in name_patterns:
        match = re.search(pattern, email_text, re.IGNORECASE | re.DOTALL)
        if match:
            result.client_name = match.group(1).strip()
            break

    # Extrakce oslovení (komu je email adresován)
    greeting_match = re.search(
        r'[Dd]obrý den\s+([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)',
        email_text
    )
    if greeting_match:
        result.greeting = greeting_match.group(1).strip()

    # Extrakce množství
    qty_patterns = [
        r'(\d[\d\s.,]*)\s*(?:ks|kusů|kusy|pcs|pieces)',
        r'(\d[\d\s.,]*)\s*(?:ks|kusů)',
    ]
    for pattern in qty_patterns:
        matches = re.findall(pattern, email_text, re.IGNORECASE)
        if matches:
            for m in matches:
                # Zpracování formátu "300,500" nebo "300, 500" jako dva samostatné počty
                parts = re.split(r'[,;]\s*', m.strip())
                for part in parts:
                    part = part.strip().replace(" ", "").replace(".", "")
                    if part.isdigit():
                        result.quantities.append(int(part))
            break

    # Pokud nebyly nalezeny s "ks", hledej samostatná čísla v kontextu
    if not result.quantities:
        qty_context = re.findall(r'(\d{2,5})\s*[,]\s*(\d{2,5})', email_text)
        for group in qty_context:
            for num in group:
                result.quantities.append(int(num))

    # Extrakce URL
    url_pattern = r'https?://[^\s<>\"\']+'
    urls = re.findall(url_pattern, email_text)
    result.urls = urls

    # Extrakce informace o potisku
    print_patterns = [
        r'(?:tisk|potisk)\s+(.+?)(?:\n|$)',
        r'(\d+)\s*(?:barv|barev|b\b)',
        r'logo\s+(\d+\s*b(?:arv)?)',
    ]
    print_parts = []
    for pattern in print_patterns:
        matches = re.findall(pattern, email_text, re.IGNORECASE)
        for m in matches:
            print_parts.append(m.strip())
    if print_parts:
        result.print_info = ", ".join(print_parts)

    # Hledání názvů produktů (klíčová slova)
    product_keywords = [
        "náplast", "náplasti", "kondom", "kondomy", "ubrousek", "ubrousky",
        "gel", "gely", "kapesník", "kapesníky", "krém", "krémy",
        "spray", "sprej", "pasta", "mýdlo", "šampon", "balzám",
        "dezinfekce", "tissues", "wipes", "pocket", "fólie",
    ]
    email_lower = email_text.lower()
    for keyword in product_keywords:
        if keyword in email_lower:
            result.products.append({"keyword": keyword, "matched": True})

    return result
