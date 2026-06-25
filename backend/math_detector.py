import re

# Common math keywords
MATH_KEYWORDS = {
    # Arithmetic
    "add", "addition", "plus", "sum",
    "subtract", "subtraction", "minus", "difference",
    "multiply", "multiplication", "times", "product",
    "divide", "division", "quotient",
    "calculate", "compute", "evaluate", "solve", "simplify",

    # Algebra
    "equation", "expression", "algebra", "linear",
    "quadratic", "polynomial", "factor", "expand",
    "variable", "coefficient", "root",

    # Geometry
    "triangle", "circle", "square", "rectangle",
    "polygon", "radius", "diameter", "circumference",
    "area", "perimeter", "volume", "surface area",
    "angle", "hypotenuse",

    # Trigonometry
    "sin", "cos", "tan", "cot", "sec", "cosec",
    "trigonometry",

    # Calculus
    "derivative", "differentiate",
    "integration", "integrate",
    "limit",

    # Statistics
    "mean", "median", "mode",
    "variance", "standard deviation",
    "probability",

    # Percentage / Ratio
    "percentage", "percent",
    "ratio", "proportion",

    # Fractions
    "fraction", "decimal",

    # Units
    "convert",
    "km", "cm", "mm", "m",
    "kg", "g", "mg",
    "litre", "liter", "ml",
    "hour", "minute", "second",

    # Misc
    "lcm", "hcf", "gcd", "prime",
    "even", "odd",
    "cube", "square root"
}

MATH_SYMBOL_PATTERN = re.compile(
    r"[+\-*/=^%√π∞≤≥<>]|"
    r"\d+\s*[+\-*/=]\s*\d+|"
    r"\b\d+\b"
)

EQUATION_PATTERN = re.compile(
    r"[a-zA-Z]\s*=\s*|"
    r"\d*x|\d*y|\d*z|"
    r"[xyz]\^?\d*"
)


def is_math_question(question: str) -> bool:
    """
    Returns True if the question is primarily mathematical.
    """

    if not question:
        return False

    text = question.lower().strip()

    if any(keyword in text for keyword in MATH_KEYWORDS):
        return True

    if MATH_SYMBOL_PATTERN.search(text):
        return True

    if EQUATION_PATTERN.search(text):
        return True

    return False