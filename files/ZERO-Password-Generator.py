#!/usr/bin/env python3
# ZERO Password Generator - strong random passwords, made on your own computer. Nothing is saved or sent.
# Needs: nothing extra (Python 3 only)
import math
import secrets
import string

LOOKALIKES = set("O0oIl1|")


def pause():
    try:
        input("\nPress Enter to close...")
    except EOFError:
        pass


def build_pool(symbols=True, avoid_lookalikes=True):
    classes = [string.ascii_lowercase, string.ascii_uppercase, string.digits]
    if symbols:
        classes.append("!@#$%^&*()-_=+[]{};:,.?")
    if avoid_lookalikes:
        classes = ["".join(c for c in cls if c not in LOOKALIKES) for cls in classes]
    return classes


def generate(length=16, symbols=True, avoid_lookalikes=True):
    classes = build_pool(symbols, avoid_lookalikes)
    length = max(length, len(classes))
    pool = "".join(classes)
    chars = [secrets.choice(cls) for cls in classes]          # at least one from every group
    chars += [secrets.choice(pool) for _ in range(length - len(chars))]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def entropy_bits(length, pool_size):
    return length * math.log2(pool_size)


def rating(bits):
    if bits < 50:
        return "weak"
    if bits < 70:
        return "okay"
    if bits < 100:
        return "strong"
    return "very strong"


def ask(prompt, default):
    value = input(f"{prompt} [{default}]: ").strip()
    return value or str(default)


def main():
    print("=== ZERO Password Generator ===")
    print("Passwords are created here on your computer and never saved or sent anywhere.\n")
    try:
        length = int(ask("Length", 16))
        count = int(ask("How many passwords", 5))
    except ValueError:
        print("Please type numbers only.")
        return pause()
    symbols = ask("Include symbols? (y/n)", "y").lower() != "n"
    clear = ask("Avoid look-alike characters like O/0 and l/1? (y/n)", "y").lower() != "n"
    pool_size = len("".join(build_pool(symbols, clear)))
    bits = entropy_bits(max(length, 4), pool_size)
    print(f"\nStrength: about {bits:.0f} bits ({rating(bits)})\n")
    for _ in range(max(1, min(count, 50))):
        print("  " + generate(length, symbols, clear))
    print("\nUse a different password for every account, and keep them in a password manager.")
    pause()


if __name__ == "__main__":
    main()
