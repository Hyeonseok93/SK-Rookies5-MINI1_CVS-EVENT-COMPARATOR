"""Event unit-price helpers shared by pages and cart."""
from __future__ import annotations


def unit_price(event: str, price: int) -> int:
    e = (event or "").replace(" ", "")
    p = int(price or 0)
    if e == "1+1":
        return p // 2
    if e == "2+1":
        return (p * 2) // 3
    if e == "3+1":
        return (p * 3) // 4
    return p


def discount_rate(event: str) -> str:
    e = (event or "").replace(" ", "")
    if e == "1+1":
        return "50%"
    if e == "2+1":
        return "33%"
    if e == "3+1":
        return "25%"
    return "0%"


def discount_num(event: str) -> float:
    e = (event or "").replace(" ", "")
    if e == "1+1":
        return 50.0
    if e == "2+1":
        return 33.0
    if e == "3+1":
        return 25.0
    return 0.0


def pay_and_total_counts(event: str) -> tuple[int, int]:
    """(pay_count, total_count) for combo math — e.g. 2+1 → (2, 3)."""
    e = (event or "").replace(" ", "")
    if e == "1+1":
        return 1, 2
    if e == "2+1":
        return 2, 3
    if e == "3+1":
        return 3, 4
    return 1, 1
