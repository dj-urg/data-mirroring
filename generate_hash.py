import os
import sys
from werkzeug.security import generate_password_hash

def generate_hash():
    print("Password Hash Generator")
    print("=======================")
    
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = input("Enter the password to hash: ").strip()
    
    if not password:
        print("Error: Password cannot be empty.")
        return

    # Use pbkdf2:sha256 which is standard in werkzeug
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    
    print("\nGenerated Hash:")
    print(f"{hashed_password}")
    print("\nAdd this line to your .env file:")
    print(f"ACCESS_CODE_HASH={hashed_password}")
    print("\nRemove the old ACCESS_CODE variable from your .env file.")

if __name__ == "__main__":
    generate_hash()
