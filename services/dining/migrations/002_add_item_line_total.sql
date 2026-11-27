ALTER TABLE dbo.visit_items
ADD line_total AS (quantity * unit_price) PERSISTED;
