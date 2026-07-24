import aiosqlite

from config import DB_NAME


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                price_rub INTEGER NOT NULL,
                photo_path TEXT,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1
            )
        """)
        await db.commit()


async def register_user(user_id: int, username: str | None):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username),
        )
        await db.commit()


async def get_categories():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT id, name FROM categories ORDER BY id")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def add_category(name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        await db.commit()


async def get_products_by_category(category_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, category_id, title, description, price_rub, photo_path "
            "FROM products WHERE category_id = ? ORDER BY id",
            (category_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_product(product_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, category_id, title, description, price_rub, photo_path "
            "FROM products WHERE id = ?",
            (product_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def add_product(category_id: int, title: str, description: str, price_rub: int, photo_path: str | None):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO products (category_id, title, description, price_rub, photo_path) "
            "VALUES (?, ?, ?, ?, ?)",
            (category_id, title, description, price_rub, photo_path),
        )
        await db.commit()


async def delete_product(product_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await db.commit()


async def add_to_cart(user_id: int, product_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )
        row = await cursor.fetchone()
        if row:
            await db.execute(
                "UPDATE cart SET quantity = quantity + 1 WHERE user_id = ? AND product_id = ?",
                (user_id, product_id),
            )
        else:
            await db.execute(
                "INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, 1)",
                (user_id, product_id),
            )
        await db.commit()


async def get_cart(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT p.id, p.title, p.price_rub, c.quantity
            FROM cart c
            JOIN products p ON p.id = c.product_id
            WHERE c.user_id = ?
            """,
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def clear_cart(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await db.commit()


async def remove_from_cart(user_id: int, product_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM cart WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )
        await db.commit()

