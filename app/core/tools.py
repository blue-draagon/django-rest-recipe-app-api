"""
Tools that will be use for helper
"""
GREEN_START = "\033[92m"
GREEN_END = "\033[0m"


def test_ok(name=""):
    print(f"...{name} {GREEN_START}OK{GREEN_END}")
