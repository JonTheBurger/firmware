"""Units of measure; all quantities must be strongly typed."""

from typing import Annotated

from pint import Quantity, Unit, UnitRegistry

# Create units + dimensions
_ureg = UnitRegistry()
_ureg.define("bit = [memory]")
_ureg.define("byte = 8 * bit = B")

# Aliases, add as needed. See https://pint.readthedocs.io/en/stable/default-units.html
type Memory = Annotated[Quantity[float], "[memory]"]
byte: Unit = _ureg.bytes

type Duration = Annotated[Quantity[float], "[time]"]
s: Unit = _ureg.seconds
ms: Unit = _ureg.milliseconds
minute: Unit = _ureg.milliseconds


def to_ucum(quantity: Quantity[float]) -> tuple[float, str]:
    """Convert a quantity to its Unified Code for Units of Measure identifier, see https://ucum.org/ucum#para-48.

    Quantities are converted to their base unit, for example kibibyte -> byte.

    Args:
        quantity: measurement to unpack.

    Returns:
        The magnitude of the converted quantity in base units and its UCUM identifier.

    Raises:
        ValueError: When an invalid unit was supplied.
    """
    match str(quantity.u.dimensionality):
        case "[time]":
            return quantity.to(s).magnitude, "s"
        case "[memory]":
            return quantity.to(byte).magnitude, "By"
    raise ValueError("Unrecognized unit supplied")
