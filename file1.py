from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import ciphers
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64
import jwt
import secrets
from cryptography.fernet import Fernet

# Secure Key Management
class SecureKeyManager:
    def __init__(self):
        self.backend = default_backend()

        # Load public and private RSA keys for secure communication
        with open("rrm-public.pem", "rb") as key_file:
            self.rrm_public_key = serialization.load_pem_public_key(
                key_file.read(),
                backend=self.backend
            )

        with open("sr-private.pem", "rb") as key_file:
            self.sr_private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=b'digitaleq',  # Make sure the private key is password protected
                backend=self.backend
            )

    def decrypt_key(self, encrypted_key):
        """Decrypt the encrypted AES key using RSA private key."""
        decoded_key = self._base64_decode(encrypted_key)
        key = self.sr_private_key.decrypt(
            decoded_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None
            )
        )
        return key

    @staticmethod
    def _base64_decode(text):
        """Base64 decode URL-safe string."""
        if len(text) % 4 != 0:
            while len(text) % 4 != 0:
                text += "="
        return base64.urlsafe_b64decode(text)

# Product Class
class Product:
    def __init__(self, product_id, name, price, quantity):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.quantity = quantity

    def update_quantity(self, quantity):
        """Update product quantity after an order."""
        self.quantity -= quantity

# Customer Class
class Customer:
    def __init__(self, customer_id, name, email, key_manager):
        self.customer_id = customer_id
        self.name = name
        self.email = email
        self.key_manager = key_manager
        self.cart = []

    def encrypt_data(self, data):
        """Encrypts plain-text data using the provided RSA and AES key."""
        aes_key = secrets.token_bytes(32)  # Generate a secure AES key
        fernet = Fernet(aes_key)  # AES encryption with Fernet
        encrypted_data = fernet.encrypt(data.encode())

        # Encrypt the AES key using RSA public key
        encrypted_key = self.key_manager.rrm_public_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None
            )
        )
        # Return the encrypted key along with the encrypted data
        return encrypted_key, encrypted_data

    def decrypt_data(self, encrypted_key, encrypted_data):
        """Decrypt encrypted data using RSA private key and AES key."""
        # Decrypt the AES key with RSA private key
        decrypted_key = self.key_manager.decrypt_key(encrypted_key)

        # Decrypt the data using AES
        fernet = Fernet(decrypted_key)
        decrypted_data = fernet.decrypt(encrypted_data).decode()
        return decrypted_data

    def add_to_cart(self, product, quantity):
        """Add an item to the customer's cart."""
        self.cart.append((product, quantity))

    def checkout(self, key_manager, payment_gateway):
        """Processes customer checkout."""
        total_amount = sum(item[0].price * item[1] for item in self.cart)
        encrypted_name, encrypted_email = self.encrypt_data(self.name)

        print(f"\nCheckout Summary for encrypted customer data:")
        print(f"Total amount: AED {total_amount:.2f}")
        print(f"Encrypted Name: {encrypted_name}")
        print(f"Encrypted Email: {encrypted_email}")

        if payment_gateway.process_payment(total_amount):
            payment_gateway.place_order(self, list(self.cart), total_amount)
            print("Order placed successfully.")
        else:
            print("Payment failed. Order not placed.")

# Payment Gateway Class
class PaymentGateway:
    def __init__(self, name):
        self.name = name

    def process_payment(self, amount):
        """Simulate payment processing."""
        print(f"Processing payment of AED {amount:.2f} through {self.name}...")
        return True

    def place_order(self, customer, order_items, total_amount):
        """Places an order and updates inventory."""
        for item in order_items:
            item[0].update_quantity(item[1])

        print(f"Order placed for {customer.name}. Total: AED {total_amount:.2f}")
        # clear the cart after placing the order
        customer.cart.clear()

# Online Shopping System Class
class OnlineShoppingSystem:
    def __init__(self):
        self.inventory = {}  # Store inventory
        self.orders = []  # Store orders
        self.customers = {}  # Store customers
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
            print(f"Order {i} for {order['customer'].name}")
            print(f"  Total Amount: AED {order['total_amount']:.2f}")
            print(f"  Items: {[f'{item[0].name} x {item[1]}' for item in order['items']]}")

# Example: Driver Code
key_manager = SecureKeyManager()

# Initialize the system
oss = OnlineShoppingSystem()

# Add some products
oss.add_product(1, "Mangoes", 2.5, 50)
oss.add_product(2, "Pineapples", 3.0, 30)

# Register customers
alice = Customer(101, "Alice", "alice@customer.com", key_manager)
bob = Customer(102, "Bob", "bob@customer.com", key_manager)

oss.customers[alice.customer_id] = alice
oss.customers[bob.customer_id] = bob

# Add to cart
alice.add_to_cart(oss.inventory[1], 5)
bob.add_to_cart(oss.inventory[2], 3)

# Display inventory and checkout
oss.display_inventory()
alice.checkout(key_manager, oss.payment_gateway)
bob.checkout(key_manager, oss.payment_gateway)

# Display orders
oss.display_orders()
