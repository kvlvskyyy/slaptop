from decimal import Decimal
from models import Category, Sticker
from extensions import db

STICKERS_DATA = [
    {
        "name": "FeedPulse Warrior",
        "price": Decimal("0.99"),
        "category_name": "Fontys",
        "description": "Only for the bravest feedback receivers",
        "image_path": "feedpulse_warrior.png",
        "stock": 0
    },
    {
        "name": "Working On Documentation",
        "price": Decimal("0.99"),
        "category_name": "Fontys",
        "description": "For those endless hours of documentation",
        "image_path": "working_on_documentation.jpg",
        "stock": 0
    },
    {
        "name": "Get More Feedback",
        "price": Decimal("0.99"),
        "category_name": "Fontys",
        "description": "Feedback = Growth",
        "image_path": "get_more_feedback.png",
        "stock": 0
    },
    {
        "name": "Tuff Baby",
        "price": Decimal("0.99"),
        "category_name": "Memes",
        "description": "The ultimate tuff baby sticker",
        "image_path": "tuffbaby.jpg",
        "stock": 0
    },
    {
        "name": "Sinterklaas",
        "price": Decimal("0.99"),
        "category_name": "Other",
        "description": "Celebrate Sinterklaas with this festive sticker",
        "image_path": "sinterklaas.jpg",
        "stock": 0
    },
]


def generate_stickers():
    for data in STICKERS_DATA:
        category = Category.query.filter_by(name=data["category_name"]).first()
        if not category:
            print(f"Category '{data['category_name']}' not found, skipping.")
            continue

        existing = Sticker.query.filter_by(name=data["name"]).first()
        if existing:
            print(f"Sticker '{data['name']}' already exists, skipping.")
            continue

        sticker = Sticker(
            name=data["name"],
            price=data["price"],
            category_id=category.id,
            description=data["description"],
            image_path=data["image_path"],
            stock=data["stock"],
            is_active=True
        )

        db.session.add(sticker)

    db.session.commit()
    print("Stickers generated successfully")