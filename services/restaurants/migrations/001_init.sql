CREATE TABLE dbo.health_probe (
    id bigint IDENTITY PRIMARY KEY, token nvarchar(40) NOT NULL
);
CREATE TABLE dbo.restaurants (
    id int IDENTITY PRIMARY KEY,
    title nvarchar(300) NOT NULL,
    category_name nvarchar(200), description nvarchar(max), address nvarchar(300),
    street nvarchar(300), city nvarchar(200), postal_code nvarchar(30),
    state nvarchar(200), country_code nvarchar(10), latitude float, longitude float,
    phone nvarchar(100), website nvarchar(2000),
    total_score float CHECK (total_score BETWEEN 0 AND 5),
    reviews_count int DEFAULT 0,
    price int CHECK (price BETWEEN 1 AND 4), menu nvarchar(max), image_url nvarchar(2000),
    created_at datetime2 NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE TABLE dbo.saved_restaurants (
    id int IDENTITY PRIMARY KEY,
    restaurant_id int NOT NULL UNIQUE REFERENCES dbo.restaurants(id) ON DELETE CASCADE,
    status nvarchar(20) NOT NULL DEFAULT 'want_to_go' CHECK (status IN ('want_to_go', 'visited')),
    rating float CHECK (rating BETWEEN 0 AND 5), notes nvarchar(2000),
    would_go_back bit, saved_at datetime2 NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE TABLE dbo.restaurant_images (
    id int IDENTITY PRIMARY KEY,
    restaurant_id int NOT NULL REFERENCES dbo.restaurants(id) ON DELETE CASCADE,
    image_url nvarchar(2000) NOT NULL
);
CREATE TABLE dbo.restaurant_emails (
    id int IDENTITY PRIMARY KEY,
    restaurant_id int NOT NULL REFERENCES dbo.restaurants(id) ON DELETE CASCADE,
    email nvarchar(320) NOT NULL
);
