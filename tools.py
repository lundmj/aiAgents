import os

status = ""

def set_status(s: str):
    global status
    status = s

def get_status() -> str:
    return status

def mul(a: float, b: float) -> float:
    return a * b

def add(a: float, b: float) -> float:
    return a + b

def sub(a: float, b: float) -> float:
    return a - b

def div(a: float, b: float) -> float:
    return a / b

def pow(a: float, b: float) -> float:
    return a ** b

def current_date() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")

