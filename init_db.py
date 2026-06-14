#!/usr/bin/env python3
"""
Database initialization script.
Creates tables and seeds sample data for the E-Commerce Inventory API.

Usage:
    python init_db.py
"""
import os
import sys

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, SessionLocal
from app.models import User, Category, Product, UserRole
from app.auth import get_password_hash


def create_tables():
    """Create all database tables."""
    print("📦 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")


def seed_data():
    """Seed the database with sample data."""
    db = SessionLocal()

    try:
        print("🌱 Seeding sample data...")

        # Check if data already exists
        if db.query(User).first():
            print("⚠️  Database already has data. Skipping seed.")
            return

        # Create admin user
        admin = User(
            email="admin@limkokwing.edu.sl",
            username="admin",
            hashed_password=get_password_hash("Admin123!"),
            full_name="System Administrator",
            role=UserRole.admin,
            is_active=True
        )
        db.add(admin)

        # Create manager user
        manager = User(
            email="manager@limkokwing.edu.sl",
            username="manager",
            hashed_password=get_password_hash("Manager123!"),
            full_name="Inventory Manager",
            role=UserRole.manager,
            is_active=True
        )
        db.add(manager)

        # Create viewer user
        viewer = User(
            email="viewer@limkokwing.edu.sl",
            username="viewer",
            hashed_password=get_password_hash("Viewer123!"),
            full_name="Store Viewer",
            role=UserRole.viewer,
            is_active=True
        )
        db.add(viewer)

        # Create categories
        categories = [
            Category(name="Electronics", description="Electronic devices and accessories", slug="electronics"),
            Category(name="Clothing", description="Apparel and fashion items", slug="clothing"),
            Category(name="Food & Beverages", description="Local and imported food products", slug="food-beverages"),
            Category(name="Home & Garden", description="Home improvement and gardening supplies", slug="home-garden"),
            Category(name="Books & Stationery", description="Educational and office supplies", slug="books-stationery"),
        ]
        for cat in categories:
            db.add(cat)

        db.flush()  # Get IDs for categories

        # Create products
        products = [
            Product(name="Wireless Bluetooth Speaker", description="Portable speaker with 12-hour battery life", sku="SPK-001", price=85.00, cost_price=45.00, quantity=50, reorder_level=10, category_id=1, weight_kg=0.5),
            Product(name="USB-C Charging Cable", description="Fast charging cable for smartphones", sku="CBL-001", price=12.50, cost_price=4.00, quantity=200, reorder_level=30, category_id=1, weight_kg=0.05),
            Product(name="Cotton T-Shirt", description="100% organic cotton t-shirt", sku="TSHT-001", price=25.00, cost_price=10.00, quantity=100, reorder_level=20, category_id=2, weight_kg=0.3),
            Product(name="Denim Jeans", description="Classic fit denim jeans", sku="JNS-001", price=55.00, cost_price=25.00, quantity=60, reorder_level=15, category_id=2, weight_kg=0.7),
            Product(name="Palm Oil (1L)", description="Pure Sierra Leone palm oil", sku="OIL-001", price=8.00, cost_price=4.50, quantity=80, reorder_level=20, category_id=3, weight_kg=1.0),
            Product(name="Cassava Flour (2kg)", description="Premium cassava flour for baking", sku="FLR-001", price=15.00, cost_price=8.00, quantity=40, reorder_level=10, category_id=3, weight_kg=2.0),
            Product(name="Garden Hose (50m)", description="Durable PVC garden hose", sku="HOS-001", price=35.00, cost_price=18.00, quantity=25, reorder_level=5, category_id=4, weight_kg=3.5),
            Product(name="LED Grow Light", description="Full spectrum LED for indoor plants", sku="LED-001", price=65.00, cost_price=35.00, quantity=15, reorder_level=5, category_id=4, weight_kg=1.2),
            Product(name="Programming Textbook", description="Python for Beginners - University Edition", sku="BK-001", price=45.00, cost_price=22.00, quantity=30, reorder_level=8, category_id=5, weight_kg=0.8),
            Product(name="A4 Notebook (Pack of 5)", description="Ruled notebooks for students", sku="NB-001", price=10.00, cost_price=4.00, quantity=150, reorder_level=25, category_id=5, weight_kg=0.6),
        ]
        for prod in products:
            db.add(prod)

        db.commit()
        print("✅ Sample data seeded successfully!")
        print("
🔑 Default login credentials:")
        print("   Admin:    username=admin    password=Admin123!")
        print("   Manager:  username=manager  password=Manager123!")
        print("   Viewer:   username=viewer   password=Viewer123!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("E-Commerce Inventory API - Database Setup")
    print("=" * 50)

    create_tables()
    seed_data()

    print("
🚀 Setup complete! Run the API with:")
    print("   uvicorn app.main:app --reload")
    print("
📚 API Documentation:")
    print("   Swagger UI: http://localhost:8000/docs")
    print("   ReDoc:      http://localhost:8000/redoc")
