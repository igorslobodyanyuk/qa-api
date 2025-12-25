import uuid
from faker import Faker
from sqlalchemy.orm import Session

from src.models import User, Category, Product, Order, UserRole, OrderStatus
from src.auth import get_password_hash

fake = Faker()


def clear_database(db: Session):
    """Remove all data from tables."""
    db.query(Order).delete()
    db.query(Product).delete()
    db.query(Category).delete()
    db.query(User).delete()
    db.commit()


def seed_database(db: Session) -> dict:
    """Seed database with test data. Returns counts of created records."""

    # Create test users with known credentials
    users = [
        User(
            email="admin@qa-test.com",
            username="admin",
            full_name="Admin User",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.admin,
        ),
        User(
            email="tester@qa-test.com",
            username="tester",
            full_name="Test User",
            hashed_password=get_password_hash("tester123"),
            role=UserRole.tester,
        ),
        User(
            email="viewer@qa-test.com",
            username="viewer",
            full_name="Viewer User",
            hashed_password=get_password_hash("viewer123"),
            role=UserRole.viewer,
        ),
    ]
    db.add_all(users)
    db.commit()

    # Create categories
    category_data = [
        ("Electronics", "Computers, phones, and gadgets"),
        ("Clothing", "Apparel and accessories"),
        ("Home & Garden", "Furniture of appliances"),
        ("Books", "Physical and digital books"),
        ("Sports", "Sports equipment and gear"),
    ]
    categories = []
    for name, desc in category_data:
        cat = Category(name=name, description=desc)
        categories.append(cat)
    db.add_all(categories)
    db.commit()

    # Create products
    products = []
    product_templates = [
        ("Laptop Pro 15", "Electronics", 1299.99, 15),
        ("Wireless Mouse", "Electronics", 49.99, 100),
        ("USB-C Hub", "Electronics", 79.99, 50),
        ("Mechanical Keyboard", "Electronics", 149.99, 30),
        ("4K Monitor", "Electronics", 399.99, 20),
        ("Cotton T-Shirt", "Clothing", 24.99, 200),
        ("Denim Jeans", "Clothing", 59.99, 150),
        ("Running Shoes", "Clothing", 89.99, 75),
        ("Winter Jacket", "Clothing", 149.99, 40),
        ("Desk Lamp", "Home & Garden", 34.99, 80),
        ("Office Chair", "Home & Garden", 249.99, 25),
        ("Plant Pot Set", "Home & Garden", 29.99, 120),
        ("Coffee Table", "Home & Garden", 199.99, 15),
        ("Python Cookbook", "Books", 44.99, 60),
        ("Design Patterns", "Books", 49.99, 45),
        ("Clean Code", "Books", 39.99, 70),
        ("Yoga Mat", "Sports", 29.99, 90),
        ("Dumbbells Set", "Sports", 79.99, 35),
        ("Tennis Racket", "Sports", 129.99, 20),
        ("Soccer Ball", "Sports", 24.99, 100),
    ]

    cat_map = {c.name: c for c in categories}
    for i, (name, cat_name, price, stock) in enumerate(product_templates):
        sku = f"SKU-{i + 1:04d}"
        product = Product(
            name=name,
            description=fake.paragraph(nb_sentences=2),
            price=price,
            stock=stock,
            sku=sku,
            category_id=cat_map[cat_name].id,
        )
        products.append(product)
    db.add_all(products)
    db.commit()

    # Create orders
    orders = []
    statuses = list(OrderStatus)
    for i in range(10):
        user = users[i % len(users)]
        order_products = fake.random_elements(products, length=fake.random_int(1, 4), unique=True)
        total = sum(p.price for p in order_products)

        order = Order(
            order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
            user_id=user.id,
            status=statuses[i % len(statuses)],
            total_amount=total,
            shipping_address=fake.address(),
            notes=fake.sentence() if fake.boolean() else None,
        )
        order.products = order_products
        orders.append(order)

    db.add_all(orders)
    db.commit()

    return {
        "users_created": len(users),
        "categories_created": len(categories),
        "products_created": len(products),
        "orders_created": len(orders),
    }
