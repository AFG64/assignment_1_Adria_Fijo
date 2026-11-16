CREATE TABLE dbo.health_probe (
    id bigint IDENTITY PRIMARY KEY, token nvarchar(40) NOT NULL
);
CREATE TABLE dbo.visits (
    id int IDENTITY PRIMARY KEY,
    saved_restaurant_id int NOT NULL,
    visit_date date NOT NULL DEFAULT CONVERT(date, SYSUTCDATETIME()),
    rating float CHECK (rating BETWEEN 0 AND 5), notes nvarchar(2000),
    total_amount decimal(12,2) CHECK (total_amount >= 0),
    number_of_people int CHECK (number_of_people > 0), would_go_back bit,
    created_at datetime2 NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE INDEX ix_visits_saved ON dbo.visits(saved_restaurant_id);
CREATE TABLE dbo.bills (
    id int IDENTITY PRIMARY KEY,
    visit_id int NOT NULL REFERENCES dbo.visits(id) ON DELETE CASCADE,
    content varbinary(max) NOT NULL,
    media_type nvarchar(100) NOT NULL,
    original_name nvarchar(255) NOT NULL,
    extracted_total decimal(12,2), extracted_text nvarchar(max),
    uploaded_at datetime2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT ck_bill_size CHECK (DATALENGTH(content) BETWEEN 1 AND 5242880)
);
CREATE TABLE dbo.visit_items (
    id int IDENTITY PRIMARY KEY,
    visit_id int NOT NULL REFERENCES dbo.visits(id) ON DELETE CASCADE,
    item_name nvarchar(300) NOT NULL,
    quantity int NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price decimal(12,2) CHECK (unit_price >= 0),
    rating float CHECK (rating BETWEEN 0 AND 5), notes nvarchar(2000)
);
