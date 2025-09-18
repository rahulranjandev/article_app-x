import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
dbHost = os.environ.get("dbHost")
dbuser = os.environ.get("dbuser")
dbpasswd = os.environ.get("dbpasswd")
dbport = os.environ.get("dbport")
db = os.environ.get("db")

print(f"Database Host: {dbHost}")
print(f"Database User: {dbuser}")
print(f"Database Port: {dbport}")
print(f"Database Name: {db}")


def create_database_connection():
    """Create and return a database connection with proper error handling"""
    try:
        # Convert port to integer if it exists
        port = int(dbport) if dbport else 3306

        connection = mysql.connector.connect(
            host=dbHost,
            user=dbuser,
            password=dbpasswd,
            port=port,
            database=db,
            autocommit=True,
        )
        print("✅ Successfully connected to MySQL database")
        return connection
    except mysql.connector.Error as err:
        print(f"❌ Error connecting to MySQL: {err}")
        return None
    except ValueError as err:
        print(f"❌ Invalid port number: {dbport}")
        return None


def validate_environment_variables():
    """Validate that all required environment variables are set"""
    required_vars = ["dbHost", "dbuser", "dbpasswd", "dbport", "db"]
    missing_vars = []

    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file and ensure all variables are set:")
        for var in required_vars:
            print(f"  {var}=your_value")
        return False

    print("✅ All environment variables are set")
    return True


def create_tables(cursor):
    """Create database tables if they don't exist"""
    try:
        # Create users table
        users_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_username (username),
            INDEX idx_email (email)
        )
        """
        cursor.execute(users_table_query)
        print("✅ Users table created/verified successfully")

        # Create articles table
        articles_table_query = """
        CREATE TABLE IF NOT EXISTS articles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            author VARCHAR(255) NOT NULL,
            body TEXT NOT NULL,
            create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_author (author),
            INDEX idx_create_date (create_date),
            FOREIGN KEY (author) REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE
        )
        """
        cursor.execute(articles_table_query)
        print("✅ Articles table created/verified successfully")

    except mysql.connector.Error as err:
        print(f"❌ Error creating tables: {err}")
        return False

    return True


def show_tables(cursor):
    """Display all tables in the database"""
    try:
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        if tables:
            print("\n📋 Tables in database:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("\n📋 No tables found in database")

    except mysql.connector.Error as err:
        print(f"❌ Error showing tables: {err}")


def describe_tables(cursor):
    """Show the structure of created tables"""
    try:
        tables = ["users", "articles"]

        for table in tables:
            print(f"\n📊 Structure of {table} table:")
            cursor.execute(f"DESCRIBE {table}")
            columns = cursor.fetchall()

            print(
                f"{'Field':<20} {'Type':<20} {'Null':<5} {'Key':<5} {'Default':<15} {'Extra'}"
            )
            print("-" * 80)

            for column in columns:
                field, field_type, null, key, default, extra = column
                default = str(default) if default is not None else "NULL"
                print(
                    f"{field:<20} {field_type:<20} {null:<5} {key:<5} {default:<15} {extra}"
                )

    except mysql.connector.Error as err:
        print(f"❌ Error describing tables: {err}")


def main():
    """Main function to set up the database"""
    print("🚀 Starting database setup...")

    # Validate environment variables
    if not validate_environment_variables():
        return

    # Create database connection
    mydb = create_database_connection()
    if not mydb:
        return

    try:
        mycursor = mydb.cursor()

        # Create tables
        if create_tables(mycursor):
            print("\n✅ All tables created successfully!")

        # Show all tables
        show_tables(mycursor)

        # Show table structures
        describe_tables(mycursor)

        print("\n✅ Database setup completed successfully!")

    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
    except Exception as err:
        print(f"❌ Unexpected error: {err}")
    finally:
        # Clean up
        if "mycursor" in locals():
            mycursor.close()
        if mydb and mydb.is_connected():
            mydb.close()
            print("🔐 Database connection closed")


if __name__ == "__main__":
    main()
