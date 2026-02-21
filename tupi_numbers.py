import os
import random
import sys

# Prefer the local pydicate package in this repo over any installed version.
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
LOCAL_PYDICATE_ROOT = os.path.join(REPO_ROOT, "pydicate")
if LOCAL_PYDICATE_ROOT not in sys.path:
    sys.path.insert(0, LOCAL_PYDICATE_ROOT)

from pydicate.lang.tupilang import *
from pydicate.lang.tupilang.pos import *
from pydicate import Predicate
from tqdm import tqdm
from tabulate import tabulate

# we will use numbers in tupi to create a base 5 number system for counting consistently and previsibly
foot = Number("amby", definition="foot", tag="[NUMBER:MAIS_5]")
tupi_numbers = {
    0: Number("ná"),
    1: îepé,
    2: mokõî,
    3: mosapyr,
    4: irundyk,
    5: mbó,
    6: mbó / îepé,
    7: mbó / mokõî,
    8: mbó / mosapyr,
    9: mbó / irundyk,
    10: opambó,
    # 11: opambó / îepé,
    # 12: opambó / mokõî,
    # 13: opambó / mosapyr,
    # 14: opambó / irundyk,
    # 15: opambó / foot,
    # 16: opambó / foot / îepé,
    # 17: opambó / foot / mokõî,
    # 18: opambó / foot / mosapyr,
    # 19: opambó / foot / irundyk,
    # 20: xe_pó_xe_py
}

tupi_space_suffix = {
    10: Noun("pambó", definition="tens place marker", tag="[PLACE_MARKER:10]"),
    100: Noun("mbopy", definition="hundreds place marker", tag="[PLACE_MARKER:100]"),
    1000: Noun("etá", definition="thousands place marker", tag="[PLACE_MARKER:1000]"),
    1_000_000: Noun(
        "gûasu", definition="millions place marker", tag="[PLACE_MARKER:1_000_000]"
    ),
}
tupi_space_suffix[10_000] = tupi_space_suffix[10] / tupi_space_suffix[1000]
tupi_space_suffix[100_000] = tupi_space_suffix[100] / tupi_space_suffix[1000]
tupi_space_suffix[10_000_000] = tupi_space_suffix[10] / tupi_space_suffix[1_000_000]
tupi_space_suffix[100_000_000] = tupi_space_suffix[100] / tupi_space_suffix[1_000_000]
tupi_space_suffix[1_000_000_000] = (
    tupi_space_suffix[1000] / tupi_space_suffix[1_000_000]
)


# Let's make a function that, given a number base 10, will convert it to tupi numbers be getting the proper digit 1-10 from tupi_numbers dict and then combine it with the suffix for the place value in tupi_numbers
def tupi_number(n):
    """Convert an integer to its Tupi number representation (base 10 decomposition)."""
    if n < 0:
        raise ValueError("Negative numbers are not supported.")
    digits = []
    temp = n
    place = 1
    while temp:
        digit = temp % 10
        digits.append((digit, place))
        temp //= 10
        place *= 10
    digits.reverse()
    dig_repr = [(d, p) for (d, p) in digits if d != 0]
    res = ""
    dig_repr_display = [(d, f"{d} * {p}") for (d, p) in dig_repr]
    if n in tupi_numbers:
        p1 = tupi_numbers[n]
    else:
        tupi_parts = []
        for d, p in dig_repr:
            if p == 1:
                tupi_parts.append(tupi_numbers[d])
            elif p == 10 and d == 1:
                tupi_parts.append(Number(tupi_space_suffix[p].eval()))
            else:
                tupi_parts.append(tupi_numbers[d] / tupi_space_suffix[p])
        if tupi_parts:
            p1 = tupi_parts[0]
            n = 1
            res = p1.eval()
            for partnext in tupi_parts[1:]:
                res += " " + partnext.eval()
        else:
            p1 = tupi_numbers[0]
    if not res:
        res = p1.eval()
    return (res, dig_repr_display)


def tupi_number_by_5(n):
    """Convert an integer to its Tupi number representation."""
    if n < 0:
        raise ValueError("Negative numbers are not supported.")
    # Get the digits of this number in base 5
    digits = []
    temp = n
    while temp:
        digits.append(temp % 5)
        temp //= 5
    dig_repr = [(x, f"{x} * 5^{i}") for (i, x) in enumerate(digits)]
    dig_repr.reverse()
    if n in tupi_numbers:
        p1 = tupi_numbers[n]
    else:
        # Convert each digit to its Tupi representation
        tupi_parts = [tupi_numbers[d[0]] for d in dig_repr]
        tupi_parts.reverse()
        # Combine the parts using multiplication and addition
        p1 = tupi_parts[0]
        n = 1
        res = p1.eval()
        for partnext in tupi_parts[1:]:
            res += " " + partnext.eval()
    return (res, dig_repr)


BASE = 20


def tupi_number_by_pt(n):
    """Convert an integer to its Tupi number representation."""
    if n < 0:
        raise ValueError("Negative numbers are not supported.")
    # Get the digits of this number in base 5
    digits = []
    temp = n
    while temp:
        digits.append(temp % BASE)
        temp //= BASE
    dig_repr = [(x, f"{x} * {BASE}^{i}") for (i, x) in enumerate(digits)]
    dig_repr.reverse()
    if n in tupi_numbers:
        p1 = tupi_numbers[n]
    else:
        # Convert each digit to its Tupi representation
        tupi_parts = [tupi_numbers[d[0]] for d in dig_repr]
        tupi_parts.reverse()
        # Combine the parts using multiplication and addition
        p1 = tupi_parts[0]
        n = 1
        res = p1.eval()
        for partnext in tupi_parts[1:]:
            res += " " + partnext.eval()
    return (res, dig_repr)


rows = []
nums_to_check = (
    list(range(0, 30 + 1))
    + list(range(40, 100 + 1, 10))
    + list(range(100, 1000 + 1, 500))
    + [
        1000,
        10_000,
        100_000,
        1_000_000,
        1_348_543,
        10_000_000,
        100_000_000,
        1_000_000_000,
    ]
)
# nums_to_check  = list(range(0, 10000 + 1, 50))

# first print out the place markers and their values
print("Tupi Place Markers:")
place_rows = []
for val in sorted(tupi_space_suffix.keys()):
    place_rows.append([val, tupi_space_suffix[val].eval()])
tl = tabulate(
    place_rows,
    headers=["Value", "Tupi Place Marker"],
    tablefmt="plain",
    stralign="left",
    numalign="right",
)
print(tl)
print()

for i in nums_to_check:
    trl = tupi_number(i)
    digits = trl[1]
    tupinum = trl[0]
    # tupinum = tupinum.replace("îepembo", "mbo")
    while "mbom" in tupinum:
        tupinum = tupinum.replace("mbom", "mom")
    tupinum = tupinum.replace("õîi", "onhi")
    tupinum = tupinum.replace("îepeirundyk", "îepeîrundyk")
    tupinum = tupinum.replace("mosapyrirundyk", "mosapirundyk")
    tupinum = tupinum.replace("momomo", "mombomo")
    dig_mult = " + ".join(map(str, [x[1] for x in reversed(digits)]))
    base_5_repr = "".join(map(str, [x[0] for x in digits]))
    rows.append([i, tupinum, base_5_repr, dig_mult])
    if i % 5 == 0 or i == 1000:
        tl = tabulate(
            rows,
            headers=["Number", "Tupi", "Base-10", "Decomposition"],
            tablefmt="plain",
            stralign="left",
            numalign="right",
        )
        # if "îepemboîepé" in tl:
        print(tl)
        print()
        rows = []
