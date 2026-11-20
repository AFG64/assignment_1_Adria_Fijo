-- sqlcmd reads local passwords via environment variables (never committed).
-- The local bootstrap generates private volume-backed hex passwords for SQL/URL safety.
USE master;
GO
IF DB_ID('picky_restaurants') IS NULL CREATE DATABASE picky_restaurants;
IF DB_ID('picky_dining') IS NULL CREATE DATABASE picky_dining;
GO
IF SUSER_ID('picky_restaurants') IS NULL
    CREATE LOGIN picky_restaurants WITH PASSWORD = '$(RESTAURANTS_PASSWORD)', CHECK_POLICY = ON;
IF SUSER_ID('picky_dining') IS NULL
    CREATE LOGIN picky_dining WITH PASSWORD = '$(DINING_PASSWORD)', CHECK_POLICY = ON;
GO
USE picky_restaurants;
IF DATABASE_PRINCIPAL_ID('picky_restaurants') IS NULL
    CREATE USER picky_restaurants FOR LOGIN picky_restaurants;
ALTER ROLE db_owner ADD MEMBER picky_restaurants;
GO
USE picky_dining;
IF DATABASE_PRINCIPAL_ID('picky_dining') IS NULL
    CREATE USER picky_dining FOR LOGIN picky_dining;
ALTER ROLE db_owner ADD MEMBER picky_dining;
GO
