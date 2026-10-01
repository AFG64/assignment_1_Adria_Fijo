PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS restaurants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category_name TEXT,
    description TEXT,
    address TEXT,
    street TEXT,
    city TEXT,
    postal_code TEXT,
    state TEXT,
    country_code TEXT,
    latitude REAL,
    longitude REAL,
    phone TEXT,
    website TEXT,
    total_score REAL CHECK (total_score >= 0 AND total_score <= 5),
    reviews_count INTEGER DEFAULT 0,
    price INTEGER CHECK (price BETWEEN 1 AND 4),
    menu TEXT,
    image_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS saved_restaurants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'want_to_go'
        CHECK (status IN ('want_to_go', 'visited')),
    rating REAL CHECK (rating >= 0 AND rating <= 5),
    notes TEXT,
    would_go_back INTEGER CHECK (would_go_back IN (0, 1)),
    saved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    saved_restaurant_id INTEGER NOT NULL,
    visit_date DATE DEFAULT CURRENT_DATE,
    rating REAL CHECK (rating >= 0 AND rating <= 5),
    notes TEXT,
    total_amount REAL CHECK (total_amount >= 0),
    number_of_people INTEGER CHECK (number_of_people > 0),
    would_go_back INTEGER CHECK (would_go_back IN (0, 1)),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (saved_restaurant_id) REFERENCES saved_restaurants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_id INTEGER NOT NULL,
    image_path TEXT NOT NULL,
    extracted_total REAL,
    extracted_text TEXT,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS visit_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,
    quantity INTEGER DEFAULT 1 CHECK (quantity > 0),
    unit_price REAL CHECK (unit_price >= 0),
    rating REAL CHECK (rating >= 0 AND rating <= 5),
    notes TEXT,
    FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS restaurant_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL,
    image_url TEXT NOT NULL,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS restaurant_emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL,
    email TEXT NOT NULL,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
);
