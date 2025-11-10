#!/usr/bin/env python3
"""
Generate a Fernet encryption key for Content Clipper

This key is used to encrypt OAuth tokens in the database.
Run this script and add the output to your .env file as FERNET_KEY
"""

from cryptography.fernet import Fernet

if __name__ == "__main__":
    key = Fernet.generate_key()
    print("\n" + "="*60)
    print("Generated Fernet Key for Content Clipper")
    print("="*60)
    print("\nAdd this to your .env file:\n")
    print(f"FERNET_KEY={key.decode()}")
    print("\n" + "="*60)
    print("\nNOTE: Keep this key secure and never commit it to git!")
    print("="*60 + "\n")
