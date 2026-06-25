import re
from enum import Enum


class MathCategory(str, Enum):
    ARITHMETIC = "arithmetic"
    ALGEBRA = "algebra"
    EQUATION = "equation"
    SIMPLIFICATION = "simplification"
    FACTORIZATION = "factorization"
    EXPANSION = "expansion"
    TRIGONOMETRY = "trigonometry"
    CALCULUS = "calculus"
    LIMIT = "limit"
    DERIVATIVE = "derivative"
    INTEGRAL = "integral"
    MATRIX = "matrix"
    VECTOR = "vector"
    VECTOR_3D = "vector_3d"
    GEOMETRY = "geometry"
    COORDINATE_GEOMETRY = "coordinate_geometry"
    CONIC_SECTION = "conic_section"
    RELATION = "relation"
    COMPLEX_NUMBER = "complex_number"
    LOGARITHM = "logarithm"
    PROBABILITY = "probability"
    STATISTICS = "statistics"
    PERMUTATION_COMBINATION = "permutation_combination"
    INEQUALITY = "inequality"
    FUNCTION = "function"
    SEQUENCE_SERIES = "sequence_series"
    BINOMIAL = "binomial"
    DIFFERENTIAL_EQUATION = "differential_equation"
    BOOLEAN_LOGIC = "boolean_logic"
    WORD_PROBLEM = "word_problem"
    THEORY = "theory"
    UNKNOWN = "unknown"


ARITHMETIC_PATTERN = re.compile(
    r"^[\d\sA-Za-z_+\-*/().%^=√π∞∫∑Σ,]+$"
)

EQUATION_PATTERN = re.compile(
    r"[a-zA-Z].*=|=.*[a-zA-Z]"
)

MATRIX_PATTERN = re.compile(
    r"\b(matrix|determinant|det|adjoint|inverse|inv|transpose|rank|eigen|eigenvalue|eigenvalues|eigenvector|eigenvectors)\b|\[\[",
    re.IGNORECASE,
)


VECTOR_PATTERN = re.compile(
    r"\b(vector|dot product|cross product|scalar product)\b",
    re.IGNORECASE
)

VECTOR_3D_PATTERN = re.compile(r"\b(3d vector|three dimensional vector|direction cosine|direction ratio|vector equation|line in space|plane)\b", re.IGNORECASE)


CALCULUS_PATTERN = re.compile(
    r"\b(limit|differentiate|derivative|integrate|integration|continuity|differentiability)\b",
    re.IGNORECASE
)

TRIG_PATTERN = re.compile(
    r"\b(sin|cos|tan|cot|sec|cosec|asin|acos|atan|trigonometry|csc|sinh|cosh|tanh|exp|abs)\b",
    re.IGNORECASE
)

GEOMETRY_PATTERN = re.compile(
    r"\b(circle|triangle|square|rectangle|polygon|radius|diameter|area|perimeter|volume|surface area|angle)\b",
    re.IGNORECASE
)

COORD_PATTERN = re.compile(
    r"\b(distance|midpoint|slope|coordinate|straight line|parabola|ellipse|hyperbola)\b",
    re.IGNORECASE
)

CONIC_PATTERN = re.compile(r"\b(circle|parabola|ellipse|hyperbola|conic|focus|directrix|eccentricity)\b", re.IGNORECASE)
RELATION_PATTERN = re.compile(r"\b(relation|reflexive|symmetric|transitive|equivalence|function mapping)\b", re.IGNORECASE)

COMPLEX_PATTERN = re.compile(
    r"\b(complex|imaginary|arg|modulus|conjugate|\bi\b)\b",
    re.IGNORECASE
)

LOG_PATTERN = re.compile(
    r"\b(log|ln|logarithm)\b",
    re.IGNORECASE
)

PROBABILITY_PATTERN = re.compile(
    r"\b(probability|random|event|sample space|bayes)\b",
    re.IGNORECASE
)

STATISTICS_PATTERN = re.compile(
    r"\b(mean|median|mode|variance|standard deviation|frequency)\b",
    re.IGNORECASE
)

PC_PATTERN = re.compile(
    r"\b(permutation|combination|ncr|npr|factorial)\b",
    re.IGNORECASE
)

INEQUALITY_PATTERN = re.compile(r"(<=|>=|<|>|!=|\binequality\b)", re.IGNORECASE)
FUNCTION_PATTERN = re.compile(
    r"\b(function|domain|range|composite|inverse function)\b|\b[a-z]\s*\(\s*[a-z]\s*\)",
    re.IGNORECASE,
)
SEQUENCE_PATTERN = re.compile(r"\b(sequence|series|arithmetic progression|geometric progression|ap|gp|nth term)\b", re.IGNORECASE)
BINOMIAL_PATTERN = re.compile(r"\b(binomial|binomial theorem)\b", re.IGNORECASE)
DIFFERENTIAL_EQUATION_PATTERN = re.compile(r"\b(differential equation|dy/dx|d2y|second order)\b", re.IGNORECASE)

BOOLEAN_PATTERN = re.compile(r"\b(boolean|logic|truth table|proposition|and|or|not|xor)\b", re.IGNORECASE)

SIMPLIFY_PATTERN = re.compile(
    r"\b(simplify|evaluate)\b",
    re.IGNORECASE
)

FACTOR_PATTERN = re.compile(
    r"\b(factor|factorize|factorise)\b",
    re.IGNORECASE
)

EXPAND_PATTERN = re.compile(
    r"\b(expand)\b",
    re.IGNORECASE
)

WORD_PROBLEM_PATTERN = re.compile(
    r"\b(write|find|show|prove|explain|state|construct|train|car|bus|apple|boy|girl|person|student|teacher|integer|number|sum|difference|product|ratio|whose|total|average|cost|price|speed|distance|time|age|years|marks|students|books|balls|coins|rupees|profit|loss)\b",
    re.IGNORECASE
)

SYMBOLIC_PATTERN = re.compile(
    r"[=+\-*/^()∫∑Σ√π∞]|dx\b|dy\b|d/dx\b|\blim\b|\b(sin|cos|tan|log|sqrt|integrate|differentiate|limit|factor|expand|sec|cosec|cot|asin|acos|atan|sinh|cosh|tanh|exp|Abs)\b",
    re.IGNORECASE,
)

PURE_SYMBOLIC_PATTERN = re.compile(
    r"^[\d\sA-Za-z_+\-*/^().=,<>{}\[\]|:&%!∫∑Σ√π∞]+$"
)

def is_symbolic_expression(question: str) -> bool:
    if not question:
        return False

    text = question.strip()

    words = re.findall(r"\b\w+\b", text)

    if (
        len(words) > 8
        and not re.search(r"[=+\-*/^]", text)
        and not re.search(r"\b(sin|cos|tan|log|sqrt|integrate|differentiate|limit|factor|expand|sec|cosec|cot|asin|acos|atan|sinh|cosh|tanh|exp|Abs)\s*\(?", text, re.IGNORECASE)
    ):
        return False

    if not PURE_SYMBOLIC_PATTERN.match(text):
        return False

    if SYMBOLIC_PATTERN.search(text):
        return True

    if re.search(r"\b[a-zA-Z]\b", text):
        return True

    return False

def _score(pattern, text: str, weight: int) -> int:
    return weight if pattern.search(text) else 0

# Aliases for common misspellings or alternate category names
CATEGORY_ALIASES = {
    "derivate": MathCategory.DERIVATIVE,
    "differentation": MathCategory.DERIVATIVE,
    "differentitate": MathCategory.DERIVATIVE,
    "differeniate": MathCategory.DERIVATIVE,
    "integration": MathCategory.INTEGRAL,
    "integretion": MathCategory.INTEGRAL,
    "intergrate": MathCategory.INTEGRAL,
    "det": MathCategory.MATRIX,
    "determinant": MathCategory.MATRIX,
    "inv": MathCategory.MATRIX,
    "inverse": MathCategory.MATRIX,
    "eigen": MathCategory.MATRIX,
    "eigenvalue": MathCategory.MATRIX,
    "eigenvector": MathCategory.MATRIX,
    "eiganvalues": MathCategory.MATRIX,
    "eiganvectors": MathCategory.MATRIX,
    "matrixes": MathCategory.MATRIX,
    "prob": MathCategory.PROBABILITY,
    "stats": MathCategory.STATISTICS,
    "trigo": MathCategory.TRIGONOMETRY,
    "calc": MathCategory.CALCULUS,
}

CATEGORY_PRIORITY = [
    MathCategory.MATRIX,
    MathCategory.DIFFERENTIAL_EQUATION,
    MathCategory.DERIVATIVE,
    MathCategory.INTEGRAL,
    MathCategory.LIMIT,
    MathCategory.CALCULUS,
    MathCategory.TRIGONOMETRY,
    MathCategory.EQUATION,
    MathCategory.ARITHMETIC,
    MathCategory.WORD_PROBLEM,
    MathCategory.LOGARITHM,
    MathCategory.COMPLEX_NUMBER,
    MathCategory.COORDINATE_GEOMETRY,
    MathCategory.CONIC_SECTION,
    MathCategory.GEOMETRY,
    MathCategory.RELATION,
    MathCategory.FUNCTION,
    MathCategory.BINOMIAL,
    MathCategory.SEQUENCE_SERIES,
    MathCategory.PERMUTATION_COMBINATION,
    MathCategory.PROBABILITY,
    MathCategory.STATISTICS,
    MathCategory.BOOLEAN_LOGIC,
    MathCategory.FACTORIZATION,
    MathCategory.EXPANSION,
    MathCategory.SIMPLIFICATION,
]

def _normalize_question_text(question: str) -> str:
    text = question.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text

def _check_alias(text: str) -> tuple[MathCategory | None, float | None]:
    for alias, category in CATEGORY_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", text):
            return category, 0.95
    return None, None

def _build_category_scores(text: str, symbolic: bool) -> dict[MathCategory, int]:
    scores = {}
    scores[MathCategory.MATRIX] = _score(MATRIX_PATTERN, text, 100)
    scores[MathCategory.VECTOR_3D] = _score(VECTOR_3D_PATTERN, text, 95)
    scores[MathCategory.VECTOR] = _score(VECTOR_PATTERN, text, 90)
    scores[MathCategory.DIFFERENTIAL_EQUATION] = _score(DIFFERENTIAL_EQUATION_PATTERN, text, 88)

    if "limit" in text:
        scores[MathCategory.LIMIT] = 86
    else:
        scores[MathCategory.LIMIT] = 0

    if "differentiate" in text or "derivative" in text:
        scores[MathCategory.DERIVATIVE] = 85
    else:
        scores[MathCategory.DERIVATIVE] = 0

    if "integrate" in text or "integration" in text:
        scores[MathCategory.INTEGRAL] = 84
    else:
        scores[MathCategory.INTEGRAL] = 0

    scores[MathCategory.CALCULUS] = _score(CALCULUS_PATTERN, text, 80)
    scores[MathCategory.TRIGONOMETRY] = _score(TRIG_PATTERN, text, 78)
    scores[MathCategory.LOGARITHM] = _score(LOG_PATTERN, text, 76)
    scores[MathCategory.COMPLEX_NUMBER] = _score(COMPLEX_PATTERN, text, 74)
    scores[MathCategory.COORDINATE_GEOMETRY] = _score(COORD_PATTERN, text, 72)
    scores[MathCategory.CONIC_SECTION] = _score(CONIC_PATTERN, text, 70)
    scores[MathCategory.GEOMETRY] = _score(GEOMETRY_PATTERN, text, 68)
    scores[MathCategory.RELATION] = _score(RELATION_PATTERN, text, 66)

    if FUNCTION_PATTERN.search(text):
        if symbolic:
            scores[MathCategory.FUNCTION] = 64
        else:
            scores[MathCategory.FUNCTION] = 0
    else:
        scores[MathCategory.FUNCTION] = 0

    scores[MathCategory.BINOMIAL] = _score(BINOMIAL_PATTERN, text, 62)
    scores[MathCategory.SEQUENCE_SERIES] = _score(SEQUENCE_PATTERN, text, 60)
    scores[MathCategory.PERMUTATION_COMBINATION] = _score(PC_PATTERN, text, 58)
    scores[MathCategory.PROBABILITY] = _score(PROBABILITY_PATTERN, text, 56)
    scores[MathCategory.STATISTICS] = _score(STATISTICS_PATTERN, text, 54)
    scores[MathCategory.BOOLEAN_LOGIC] = _score(BOOLEAN_PATTERN, text, 52)
    scores[MathCategory.FACTORIZATION] = _score(FACTOR_PATTERN, text, 50)
    scores[MathCategory.EXPANSION] = _score(EXPAND_PATTERN, text, 48)
    scores[MathCategory.SIMPLIFICATION] = _score(SIMPLIFY_PATTERN, text, 46)
    scores[MathCategory.EQUATION] = _score(EQUATION_PATTERN, text, 44)
    scores[MathCategory.ARITHMETIC] = _score(ARITHMETIC_PATTERN, text, 40)

    if WORD_PROBLEM_PATTERN.search(text):
        if not symbolic:
            scores[MathCategory.WORD_PROBLEM] = 20
        else:
            scores[MathCategory.WORD_PROBLEM] = 0
    else:
        scores[MathCategory.WORD_PROBLEM] = 0

    return scores

def classify_math_question_with_confidence(question: str) -> tuple[MathCategory, float]:
    if not question:
        return MathCategory.UNKNOWN, 0.0

    text = _normalize_question_text(question)

    alias_cat, alias_conf = _check_alias(text)
    if alias_cat is not None:
        return alias_cat, alias_conf

    if MATRIX_PATTERN.search(text) and "[[" in text:
        return MathCategory.MATRIX, 1.0
    if "[[" in text:
        return MathCategory.MATRIX, 1.0

    symbolic = is_symbolic_expression(question)

    scores = _build_category_scores(text, symbolic)

    # Filter out zero and negative scores
    filtered_scores = {k: v for k, v in scores.items() if v > 0}
    if filtered_scores:
        max_score = max(filtered_scores.values())
        # Find all categories with max_score
        max_cats = [k for k, v in filtered_scores.items() if v == max_score]
        chosen_cat = max_cats[0]
        for cat in CATEGORY_PRIORITY:
            if cat in max_cats:
                chosen_cat = cat
                break
        confidence = min(max_score / 100.0, 1.0)
        return chosen_cat, confidence

    return MathCategory.UNKNOWN, 0.0


# New function: detect_math_topics

def _category_priority_index(category: MathCategory) -> int:
    try:
        return CATEGORY_PRIORITY.index(category)
    except ValueError:
        return len(CATEGORY_PRIORITY)

def detect_math_topics(question: str) -> list[MathCategory]:
    if not question:
        return []
    text = _normalize_question_text(question)

    alias_cat, _ = _check_alias(text)
    if alias_cat is not None:
        return [alias_cat]

    if MATRIX_PATTERN.search(text) and "[[" in text:
        return [MathCategory.MATRIX]
    if "[[" in text:
        return [MathCategory.MATRIX]

    symbolic = is_symbolic_expression(question)

    scores = _build_category_scores(text, symbolic)

    filtered_scores = {k: v for k, v in scores.items() if v > 0}
    if not filtered_scores:
        return []
    # Sort by descending score, then by CATEGORY_PRIORITY order for ties

    sorted_cats = sorted(
        filtered_scores.items(),
        key=lambda item: (-item[1], _category_priority_index(item[0]))
    )
    return [cat for cat, _ in sorted_cats]

def explain_classification(question: str) -> dict:
    if not question:
        return {
            "category": MathCategory.UNKNOWN,
            "confidence": 0.0,
            "matched_patterns": [],
            "matched_alias": None,
            "all_topics": [],
        }

    text = _normalize_question_text(question)

    alias_cat, alias_conf = _check_alias(text)

    category, confidence = classify_math_question_with_confidence(question)
    topics = detect_math_topics(question)

    matched_patterns = []

    pattern_map = [
        (MATRIX_PATTERN, MathCategory.MATRIX),
        (VECTOR_3D_PATTERN, MathCategory.VECTOR_3D),
        (VECTOR_PATTERN, MathCategory.VECTOR),
        (DIFFERENTIAL_EQUATION_PATTERN, MathCategory.DIFFERENTIAL_EQUATION),
        (CALCULUS_PATTERN, MathCategory.CALCULUS),
        (TRIG_PATTERN, MathCategory.TRIGONOMETRY),
        (LOG_PATTERN, MathCategory.LOGARITHM),
        (COMPLEX_PATTERN, MathCategory.COMPLEX_NUMBER),
        (COORD_PATTERN, MathCategory.COORDINATE_GEOMETRY),
        (CONIC_PATTERN, MathCategory.CONIC_SECTION),
        (GEOMETRY_PATTERN, MathCategory.GEOMETRY),
        (RELATION_PATTERN, MathCategory.RELATION),
        (FUNCTION_PATTERN, MathCategory.FUNCTION),
        (BINOMIAL_PATTERN, MathCategory.BINOMIAL),
        (SEQUENCE_PATTERN, MathCategory.SEQUENCE_SERIES),
        (PC_PATTERN, MathCategory.PERMUTATION_COMBINATION),
        (PROBABILITY_PATTERN, MathCategory.PROBABILITY),
        (STATISTICS_PATTERN, MathCategory.STATISTICS),
        (BOOLEAN_PATTERN, MathCategory.BOOLEAN_LOGIC),
        (FACTOR_PATTERN, MathCategory.FACTORIZATION),
        (EXPAND_PATTERN, MathCategory.EXPANSION),
        (SIMPLIFY_PATTERN, MathCategory.SIMPLIFICATION),
        (EQUATION_PATTERN, MathCategory.EQUATION),
        (ARITHMETIC_PATTERN, MathCategory.ARITHMETIC),
        (WORD_PROBLEM_PATTERN, MathCategory.WORD_PROBLEM),
    ]

    for pattern, cat in pattern_map:
        if pattern.search(text):
            matched_patterns.append(cat.value)

    # Deduplicate matched_patterns while preserving order
    seen = set()
    deduped_patterns = []
    for p in matched_patterns:
        if p not in seen:
            seen.add(p)
            deduped_patterns.append(p)

    matched_alias = None
    if alias_cat is not None:
        for alias, cat in CATEGORY_ALIASES.items():
            if cat == alias_cat and re.search(rf"\b{re.escape(alias)}\b", text):
                matched_alias = alias
                break

    return {
        "category": category,
        "confidence": confidence,
        "matched_patterns": deduped_patterns,
        "matched_alias": matched_alias,
        "all_topics": topics,
    }

def classify_math_question(question: str) -> MathCategory:
    category, _ = classify_math_question_with_confidence(question)
    return category