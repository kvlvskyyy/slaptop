from decimal import Decimal
from models import Category, Sticker
from extensions import db

STICKERS_DATA = [
    {
        "name": "FeedPulse Warrior",
        "price": Decimal("0.49"),
        "category_name": "Fontys",
        "description": "Only for the bravest FeedPulse users",
        "image_url": "feedpulse_warrior.webp",
        "stock": 0
    },
    {
        "name": "Working On Documentation",
        "price": Decimal("0.49"),
        "category_name": "Fontys",
        "description": "For those endless hours of documentation",
        "image_url": "working_on_documentation.webp",
        "stock": 0
    },
    {
        "name": "Get More Feedback",
        "price": Decimal("0.49"),
        "category_name": "Fontys",
        "description": "Feedback = Growth",
        "image_url": "get_more_feedback.webp",
        "stock": 0
    },
    {
        "name": "Awkward Cat",
        "price": Decimal("0.49"),
        "category_name": "Memes",
        "description": "Cute awkward cat sticker",
        "image_url": "AwkwardCat.webp",
        "stock": 0
    },
    {
        "name": "Stickerdom Logo",
        "price": Decimal("0.49"),
        "category_name": "Other",
        "description": "Stickerdom official logo sticker",
        "image_url": "Logo.webp",
        "stock": 0
    },
    {
        "name": "I Love FeedPulse",
        "price": Decimal("0.49"),
        "category_name": "Fontys",
        "description": "Show your love for FeedPulse",
        "image_url": "feedpulselove.webp",
        "stock": 14
    },
    {
        "name": "Coughing cat",
        "price": Decimal("0.49"),
        "category_name": "Memes",
        "description": "A cat who is coughing",
        "image_url": "coughing_cat.webp",
        "stock": 11
    },
    {
        "name": "Ehm, actually..",
        "price": Decimal("0.49"),
        "category_name": "Memes",
        "description": "For all the nerds",
        "image_url": "actually.webp",
        "stock": 17
    },
    {
        "name": "Skyrim skeleton",
        "price": Decimal("0.49"),
        "category_name": "Memes",
        "description": "The skyrim skeleton meme Warning⚠️: peeling off the sticker may be difficult, handle with care",
        "image_url": "SkyrimSkeletonSticker.webp",
        "stock": 19
    },
    {
        "name": "ICT Mimic",
        "price": Decimal("0.49"),
        "category_name": "Games",
        "description": "A DnD related sticker about a mimic coming out of a laptop.",
        "image_url": "mimicLaptop.webp",
        "stock": 20
    },
    {
        "name": "Last day of the project",
        "price": Decimal("0.49"),
        "category_name": "Fontys",
        "description": "Very depressing and stressful",
        "image_url": "lastdayi.webp",
        "stock": 20
    }

]
def clear_stickers():
    db.session.query(Sticker).delete()
    db.session.commit()

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