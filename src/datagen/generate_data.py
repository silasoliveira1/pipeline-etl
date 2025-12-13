import os
import random
import time
import requests
import pg8000.dbapi
from faker import Faker
from datetime import datetime

# Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "sales_db")
DB_USER = os.getenv("DB_USER", "sales_user")
DB_PASS = os.getenv("DB_PASS", "sales_password")

fake = Faker('pt_BR')

def get_db_connection():
    max_retries = 5
    for attempt in range(max_retries):
        try:
            conn = pg8000.dbapi.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
                port=DB_PORT
            )
            return conn
        except Exception as e:
            print(f"Connection failed (Attempt {attempt+1}/{max_retries}): {e}")
            time.sleep(5)
    raise Exception("Could not connect to the database")

def create_initial_products(cursor):
    """Fetches products from Fake Store API or generates them if API fails"""
    # pg8000 might require execute params to be a list/tuple
    try:
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
    except Exception:
        # Table might not exist or other error
        count = 0
    
    if count > 0:
        print(f"Products table already has {count} items. Skipping initial population.")
        return

    print("Fetching products from Fake Store API...")
    try:
        response = requests.get('https://fakestoreapi.com/products')
        products = response.json()
        
        for p in products:
            cursor.execute("""
                INSERT INTO products (product_name, category, price)
                VALUES (%s, %s, %s)
            """, (p['title'][:200], p['category'][:100], p['price']))
        print(f"Inserted {len(products)} products from API.")
        
    except Exception as e:
        print(f"API fetch failed: {e}. Generating fake products locally.")
        for _ in range(20):
            cursor.execute("""
                INSERT INTO products (product_name, category, price)
                VALUES (%s, %s, %s)
            """, (fake.bs().title(), fake.word(), round(random.uniform(10.0, 500.0), 2)))

def create_customer(cursor):
    """Creates a new random customer"""
    first_name = fake.first_name()
    last_name = fake.last_name()
    email = f"{first_name.lower()}.{last_name.lower()}@{fake.free_email_domain()}"
    email = f"{random.randint(1000,9999)}{email}" 
    
    cursor.execute("""
        INSERT INTO customers (first_name, last_name, email, phone)
        VALUES (%s, %s, %s, %s)
        RETURNING customer_id
    """, (first_name, last_name, email, fake.phone_number()))
    return cursor.fetchone()[0]

def create_order(cursor, customer_id):
    """Creates an order for a customer with random items"""
    status_list = ['completed', 'pending', 'shipped', 'cancelled']
    status = random.choice(status_list)
    
    cursor.execute("""
        INSERT INTO orders (customer_id, status, total_amount)
        VALUES (%s, %s, 0)
        RETURNING order_id
    """, (customer_id, status))
    order_id = cursor.fetchone()[0]
    
    # Add Items
    cursor.execute("SELECT product_id, price FROM products ORDER BY RANDOM() LIMIT %s", (random.randint(1, 5),))
    items = cursor.fetchall()
    
    total_amount = 0
    for product_id, price in items:
        quantity = random.randint(1, 4)
        total_amount += (float(price) * quantity)
        
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, unit_price)
            VALUES (%s, %s, %s, %s)
        """, (order_id, product_id, quantity, price))
        
    # Update Order Total
    cursor.execute("UPDATE orders SET total_amount = %s WHERE order_id = %s", (total_amount, order_id))
    return order_id

def main():
    print("Starting Data Generator...")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SET search_path TO sales")
    
    try:
        # 1. Ensure products exist
        create_initial_products(cur)
        conn.commit()
        
        # 2. Generate random activity
        num_sales = random.randint(3, 8)
        print(f"Generating {num_sales} new sales transactions...")
        
        for _ in range(num_sales):
            if random.random() < 0.2:
                customer_id = create_customer(cur)
            else:
                cur.execute("SELECT customer_id FROM customers ORDER BY RANDOM() LIMIT 1")
                res = cur.fetchone()
                if res:
                    customer_id = res[0]
                else:
                    customer_id = create_customer(cur)
            
            order_id = create_order(cur, customer_id)
            print(f"Created Order #{order_id} for Customer #{customer_id}")
            
        conn.commit()
        print("Done.")
        
    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
