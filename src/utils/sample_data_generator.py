"""
Sample Data Generator for Testing

This script generates sample data that mimics Salla API responses for testing purposes.
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict


class SampleDataGenerator:
    """Generate sample data for testing the ETL pipeline."""
    
    def __init__(self, seed: int = 42):
        """Initialize generator with random seed for reproducibility."""
        random.seed(seed)
        
        self.first_names = ['Ahmed', 'Mohammed', 'Fatima', 'Aisha', 'Omar', 'Sara', 'Ali', 'Layla']
        self.last_names = ['Al-Rashid', 'Al-Saud', 'Al-Harbi', 'Al-Otaibi', 'Al-Zahrani', 'Al-Qahtani']
        self.cities = ['Riyadh', 'Jeddah', 'Mecca', 'Medina', 'Dammam', 'Khobar']
        self.product_names = [
            'Traditional Thobe', 'Designer Abaya', 'Premium Dates', 'Arabic Coffee Set',
            'Silver Jewelry', 'Perfume Gift Set', 'Prayer Mat', 'Wall Art Calligraphy'
        ]
        self.payment_methods = ['Credit Card', 'Debit Card', 'Apple Pay', 'Cash on Delivery']
        self.shipping_methods = ['Standard Delivery', 'Express Delivery', 'Same Day Delivery']
        self.order_statuses = ['pending', 'processing', 'completed', 'cancelled']
    
    def generate_customers(self, count: int = 100) -> List[Dict]:
        """Generate sample customer data."""
        customers = []
        
        for i in range(1, count + 1):
            first_name = random.choice(self.first_names)
            last_name = random.choice(self.last_names)
            
            customer = {
                'id': i,
                'first_name': first_name,
                'last_name': last_name,
                'email': f"{first_name.lower()}.{last_name.lower()}{i}@example.com",
                'mobile': f"+966{random.randint(500000000, 599999999)}",
                'mobile_code': '+966',
                'country': 'Saudi Arabia',
                'city': random.choice(self.cities),
                'gender': random.choice(['male', 'female']),
                'birthday': self._random_date(datetime(1970, 1, 1), datetime(2005, 12, 31)).strftime('%Y-%m-%d'),
                'avatar': f"https://example.com/avatars/user_{i}.jpg",
                'addresses': [
                    {
                        'address': f"{random.randint(1, 999)} Main Street",
                        'city': random.choice(self.cities),
                        'country': 'Saudi Arabia',
                        'postal_code': f"{random.randint(10000, 99999)}"
                    }
                ],
                'created_at': self._random_date(datetime(2020, 1, 1), datetime(2024, 1, 1)).isoformat(),
                'updated_at': datetime.now().isoformat(),
                'status': 'active',
                'notes': None
            }
            customers.append(customer)
        
        return customers
    
    def generate_products(self, count: int = 50) -> List[Dict]:
        """Generate sample product data."""
        products = []
        
        for i in range(1, count + 1):
            base_price = random.uniform(50, 1000)
            sale_price = base_price * random.uniform(0.7, 0.95)
            cost_price = base_price * random.uniform(0.4, 0.6)
            
            product = {
                'id': i,
                'name': f"{random.choice(self.product_names)} - Model {i}",
                'description': f"High quality {random.choice(self.product_names).lower()} with premium features and excellent craftsmanship.",
                'price': round(base_price, 2),
                'sale_price': round(sale_price, 2) if random.random() > 0.5 else None,
                'cost_price': round(cost_price, 2),
                'sku': f"SKU-{i:05d}",
                'quantity': random.randint(0, 500),
                'unlimited_quantity': random.random() < 0.1,
                'status': random.choice(['available', 'out_of_stock', 'discontinued']),
                'type': random.choice(['physical', 'digital']),
                'weight': round(random.uniform(0.1, 10), 2),
                'weight_unit': 'kg',
                'images': [
                    f"https://example.com/products/product_{i}_1.jpg",
                    f"https://example.com/products/product_{i}_2.jpg"
                ],
                'categories': [
                    {'id': random.randint(1, 10), 'name': 'Category Name'}
                ],
                'options': [],
                'metadata_title': f"{random.choice(self.product_names)} - Best Quality",
                'metadata_description': f"Buy premium {random.choice(self.product_names).lower()} at best prices",
                'created_at': self._random_date(datetime(2020, 1, 1), datetime(2024, 1, 1)).isoformat(),
                'updated_at': datetime.now().isoformat(),
                'with_tax': True,
                'is_taxable': True,
                'require_shipping': random.choice([True, False])
            }
            products.append(product)
        
        return products
    
    def generate_orders(self, count: int = 200, customer_ids: List[int] = None, product_ids: List[int] = None) -> List[Dict]:
        """Generate sample order data."""
        if customer_ids is None:
            customer_ids = list(range(1, 101))
        if product_ids is None:
            product_ids = list(range(1, 51))
        
        orders = []
        
        for i in range(1, count + 1):
            customer_id = random.choice(customer_ids)
            num_items = random.randint(1, 5)
            
            # Generate order items
            items = []
            subtotal = 0
            for _ in range(num_items):
                product_id = random.choice(product_ids)
                quantity = random.randint(1, 3)
                unit_price = random.uniform(50, 500)
                item_total = unit_price * quantity
                
                items.append({
                    'product_id': product_id,
                    'quantity': quantity,
                    'price': round(unit_price, 2),
                    'total': round(item_total, 2)
                })
                subtotal += item_total
            
            discount = subtotal * random.uniform(0, 0.2)
            tax = (subtotal - discount) * 0.15  # 15% VAT
            shipping = random.choice([0, 20, 50])
            total = subtotal - discount + tax + shipping
            
            first_name = random.choice(self.first_names)
            last_name = random.choice(self.last_names)
            city = random.choice(self.cities)
            
            order = {
                'id': i,
                'reference_id': f"ORD-{i:06d}",
                'status': random.choice(self.order_statuses),
                'amount': round(subtotal, 2),
                'currency': 'SAR',
                'customer_id': customer_id,
                'customer_name': f"{first_name} {last_name}",
                'customer_email': f"{first_name.lower()}.{last_name.lower()}@example.com",
                'customer_mobile': f"+966{random.randint(500000000, 599999999)}",
                'payment_method': random.choice(self.payment_methods),
                'shipping_method': random.choice(self.shipping_methods),
                'shipping_address': {
                    'address': f"{random.randint(1, 999)} Main Street",
                    'city': city,
                    'country': 'Saudi Arabia',
                    'postal_code': f"{random.randint(10000, 99999)}"
                },
                'items': items,
                'created_at': self._random_date(datetime(2023, 1, 1), datetime.now()).isoformat(),
                'updated_at': datetime.now().isoformat(),
                'notes': None if random.random() > 0.3 else "Special delivery instructions",
                'coupon_code': None if random.random() > 0.3 else f"SAVE{random.randint(10, 50)}",
                'discount_amount': round(discount, 2),
                'tax_amount': round(tax, 2),
                'shipping_cost': shipping,
                'total_amount': round(total, 2)
            }
            orders.append(order)
        
        return orders
    
    def _random_date(self, start: datetime, end: datetime) -> datetime:
        """Generate random date between start and end."""
        delta = end - start
        random_days = random.randint(0, delta.days)
        return start + timedelta(days=random_days)
    
    def save_to_json(self, data: List[Dict], filename: str):
        """Save data to JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(data)} records to {filename}")


if __name__ == "__main__":
    import os
    
    # Create sample data directory
    sample_dir = os.path.join(os.path.dirname(__file__), '../../sample_data')
    os.makedirs(sample_dir, exist_ok=True)
    
    # Generate sample data
    generator = SampleDataGenerator()
    
    customers = generator.generate_customers(100)
    generator.save_to_json(customers, os.path.join(sample_dir, 'customers.json'))
    
    products = generator.generate_products(50)
    generator.save_to_json(products, os.path.join(sample_dir, 'products.json'))
    
    customer_ids = [c['id'] for c in customers]
    product_ids = [p['id'] for p in products]
    orders = generator.generate_orders(200, customer_ids, product_ids)
    generator.save_to_json(orders, os.path.join(sample_dir, 'orders.json'))
    
    print("\nSample data generation complete!")
    print(f"Generated {len(customers)} customers, {len(products)} products, and {len(orders)} orders")
