"""SQLAlchemy modely."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Product(Base):
    """Produkt v katalogu."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    category = Column(String(100), default="")
    image_url = Column(String(500), default="")
    image_local = Column(String(500), default="")
    shipping_cost = Column(Float, default=0.0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    price_tiers = relationship("PriceTier", back_populates="product", cascade="all, delete-orphan",
                               order_by="PriceTier.min_quantity")

    def get_price_for_quantity(self, quantity: int) -> float | None:
        """Vrátí jednotkovou cenu pro dané množství."""
        for tier in self.price_tiers:
            if tier.min_quantity <= quantity <= (tier.max_quantity or 999999):
                return tier.price_per_unit
        return None

    def get_image(self) -> str:
        """Vrátí URL obrázku (lokální nebo vzdálený)."""
        if self.image_local:
            return f"/static/uploads/{self.image_local}"
        return self.image_url or ""


class PriceTier(Base):
    """Cenový stupeň produktu."""
    __tablename__ = "price_tiers"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    min_quantity = Column(Integer, nullable=False)
    max_quantity = Column(Integer, nullable=True)
    price_per_unit = Column(Float, nullable=False)

    product = relationship("Product", back_populates="price_tiers")


class Quote(Base):
    """Vygenerovaná nabídka."""
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(255), default="")
    client_email = Column(Text, default="")
    original_email = Column(Text, default="")
    email_reply = Column(Text, default="")
    pdf_path = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("QuoteItem", back_populates="quote", cascade="all, delete-orphan")

    @property
    def total_without_vat(self) -> float:
        return sum(item.total_price for item in self.items)

    @property
    def total_with_vat(self) -> float:
        return self.total_without_vat * 1.21


class QuoteItem(Base):
    """Položka nabídky."""
    __tablename__ = "quote_items"

    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    note = Column(String(500), default="")

    quote = relationship("Quote", back_populates="items")
    product = relationship("Product")
