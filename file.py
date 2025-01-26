from cryptography.fernet import Fernet
import matplotlib.pyplot as plt
import csv
import os

# Key Management
def generate_key():
    """Generates and saves an encryption key."""
    key = Fernet.generate_key()
    # Avoid saving the key in a file for better security (environment variable is preferred in production)
    os.environ["FERNET_KEY"] = key.decode()  # Save the key in environment variable
    print("Encryption key generated and saved to environment variable.")

def load_key():
    """Loads the encryption key from the environment variable."""
    key = os.getenv("FERNET_KEY")
    if key:
        return key.encode()
    else:
        print("Encryption key not found. Please generate a key first.")
        return None

# Encryption and Decryption
def encrypt_data(data, key):
    """Encrypts plain-text data using the provided encryption key."""
    fernet = Fernet(key)
    return fernet.encrypt(data.encode())

def decrypt_data(encrypted_data, key):
    """Decrypts encrypted data using the provided encryption key."""
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_data).decode()

class Product:
    def __init__(self, product_id, name, price, quantity):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.quantity = quantity

    def update_quantity(self, quantity):
        """Update product quantity after an order."""
        self.quantity -= quantity

class Item:
    def __init__(self, product, quantity):
        self.product = product
        self.quantity = quantity

    def total_price(self):
        """Calculate the total price for the item."""
        return self.product.price * self.quantity

class Customer:
    def __init__(self, customer_id, name, email, key):
        self.customer_id = customer_id
        self.name = encrypt_data(name, key)
        self.email = encrypt_data(email, key)
        self.cart = []

    def decrypt_name(self, key):
        return decrypt_data(self.name, key)

    def decrypt_email(self, key):
        return decrypt_data(self.email, key)

    def add_to_cart(self, product, quantity):
        """Add an item to the customer's cart."""
        self.cart.append(Item(product, quantity))

    def checkout(self, key, payment_gateway):
        """Processes customer checkout."""
        total_amount = sum(item.total_price() for item in self.cart)
        decrypted_name = self.decrypt_name(key)
        print(f"\nCheckout Summary for {decrypted_name}")
        print(f"Total amount: AED {total_amount:.2f}")

        #pass both the order items (cart) and the total amount to place_order()
        if payment_gateway.process_payment(total_amount):
            payment_gateway.place_order(self, list(self.cart), total_amount)  #pass the cart items as a copy
            print("Order placed successfully.")
        else:
            print("Payment failed. Order not placed.")

    @staticmethod
    def register_customer(customer_id, name, email, key):
        """Registers a customer with encrypted sensitive information."""
        return Customer(customer_id, name, email, key)

class PaymentGateway:
    def __init__(self, name):
        self.name = name

    def process_payment(self, amount):
        """Simulates payment processing."""
        print(f"Processing payment of AED {amount:.2f} through {self.name}...")
        return True

    def place_order(self, customer, order_items, total_amount):
        """Places an order and updates inventory."""
        # Add items to the order first, then update inventory
        for item in order_items:
            item.product.update_quantity(item.quantity)

        order_details = {
            'customer': customer,
            'items': order_items,
            'total_amount': total_amount
        }

        oss.orders.append(order_details)  #append the order to the orders list
        print(f"Order {len(oss.orders)} for {customer.decrypt_name(key)} added.")  # Debug print

        #clear the cart after the order is successfully processed
        customer.cart.clear()

class OnlineShoppingSystem:
    def __init__(self):
        self.inventory = {} #store inventory
        self.orders = []  #store orders
        self.customers = {} #customers
        self.payment_gateway = PaymentGateway("SecurePaymentGateway")

    def add_product(self, product_id, name, price, quantity):
        """Adds a product to the inventory."""
        product = Product(product_id, name, price, quantity)
        self.inventory[product_id] = product

    def display_inventory(self):
        """Displays the current inventory."""
        print("\nInventory:")
        for product in self.inventory.values():
            print(f"ID: {product.product_id}, Name: {product.name}, Price: AED {product.price:.2f}, Quantity: {product.quantity}")

    def display_orders(self):
        """Displays all orders."""
        print("\nOrders:")
        for i, order in enumerate(self.orders, start=1):
            print(f"Order {i} for {order['customer'].decrypt_name(key)}")
            print(f"  Total Amount: AED {order['total_amount']:.2f}")
            print(f"  Items: {[f'{item.product.name} x {item.quantity}' for item in order['items']]}")

    def save_customers_to_csv(self, filename="customers.csv"):
        """Saves customer data to a CSV file."""
        with open(filename, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Customer ID", "Name (Encrypted)", "Email (Encrypted)"])
            for customer in self.customers.values():
                writer.writerow([customer.customer_id, customer.name, customer.email])
        print(f"Customer data saved to '{filename}'.")

    def save_orders_to_csv(self, filename="orders.csv"):
        """Saves order data to a CSV file."""
        with open(filename, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Order ID", "Customer ID", "Items", "Total Amount (AED)"])
            
            for i, order in enumerate(self.orders, start=1):
                # Add debug print here to check order details
                print(f"Saving Order {i}: {order['customer'].decrypt_name(key)}")
                
                # Extract and format items properly
                items = "; ".join([f"{item.product.name} x {item.quantity}" for item in order['items']])
                print(f"Items in Order {i}: {items}")  # Debug print to check item details
                
                writer.writerow([i, order['customer'].customer_id, items, order['total_amount']])
        
        print(f"Order data saved to '{filename}'.")


    def plot_inventory(self):
        """Plots the inventory levels."""
        products = [product.name for product in self.inventory.values()]
        quantities = [product.quantity for product in self.inventory.values()]

        plt.bar(products, quantities)
        plt.xlabel('Products')
        plt.ylabel('Quantity')
        plt.title('Inventory Levels')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig("inventory_plot.png")  # Save the plot
        plt.show()
        print("Inventory graph saved as 'inventory_plot.png'.")

    def plot_orders(self):
        """Plots the total amounts for orders."""
        if len(self.orders) == 0:
            print("No orders to plot.")
            return

        order_ids = list(range(1, len(self.orders) + 1))
        order_totals = [order["total_amount"] for order in self.orders]

        plt.plot(order_ids, order_totals, marker='o')
        plt.xlabel('Order ID')
        plt.ylabel('Total Amount (AED)')
        plt.title('Order Totals')
        plt.savefig("orders_plot.png")  # Save the plot
        plt.show()
        print("Orders graph saved as 'orders_plot.png'.")

# Driver code
user_choice = input("Do you want to generate a new encryption key? (yes/no): ").strip().lower()
if user_choice == "yes":
    generate_key()

key = load_key()  # Load encryption key
if not key:
    print("Key loading failed. Exiting application.")
    exit()

# Initialize system
oss = OnlineShoppingSystem()

# Add products to inventory
products = [
    (1, "Mangoes", 2.5, 50), (2, "Pineapples", 3.0, 30),
    (3, "Pomegranates", 4.0, 20), (4, "Cherries", 5.0, 15),
    (5, "Watermelons", 7.0, 10), (6, "Peaches", 2.8, 25),
    (7, "Blueberries", 6.5, 40), (8, "Grapes", 3.5, 35)
]
for product in products:
    oss.add_product(*product)

# Register customers
alice = Customer.register_customer(101, "Alice", "alice@customer.com", key)
bob = Customer.register_customer(102, "Bob", "bob@customer.com", key)

oss.customers[alice.customer_id] = alice
oss.customers[bob.customer_id] = bob

# Add to cart
alice.add_to_cart(oss.inventory[1], 5)
alice.add_to_cart(oss.inventory[2], 3)
bob.add_to_cart(oss.inventory[3], 4)

# Display inventory and checkout
oss.display_inventory()
alice.checkout(key, oss.payment_gateway)
bob.checkout(key, oss.payment_gateway)

# Display orders and save to CSV
oss.display_orders()
oss.save_customers_to_csv()
oss.save_orders_to_csv()

# Plot inventory and orders
oss.plot_inventory()
oss.plot_orders()
