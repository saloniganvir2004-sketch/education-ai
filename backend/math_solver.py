import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr
from openai import OpenAI
from config import settings
from answer_translator import translate_answer
from math_router import classify_math_question, MathCategory
client = OpenAI(api_key=settings.OPENAI_API_KEY)
SYMPY_EXECUTOR = ThreadPoolExecutor(max_workers=4)


# --- Expression cleaning helpers ---

def _tokenize_math_input(question: str) -> list[str]:
    """
    Convert input to lowercase and split into tokens, preserving math operators and delimiters as separate tokens.
    """
    # Lowercase first
    s = question.lower()
    # Add spaces around operators and delimiters to split them as tokens
    # Operators: + - * / ^ ( ) = , [ ]
    s = re.sub(r"([\+\-\*/\^\(\)=,\[\]])", r" \1 ", s)
    # Remove extra spaces and split
    tokens = s.split()
    return tokens

def _normalize_tokens(tokens: list[str]) -> list[str]:
    """
    Normalize tokens: keyword normalization, symbol replacement, function normalization, etc.
    """
    normalized = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        # Replace unicode and alternate operator symbols
        if t in {"÷"}:
            normalized.append("/")
        elif t in {"×"}:
            normalized.append("*")
        elif t in {"−", "–"}:
            normalized.append("-")
        elif t == "π":
            normalized.append("pi")
        elif t == "∞":
            normalized.append("oo")
        elif t == "phi":
            normalized.append("GoldenRatio")
        elif t == "^":
            normalized.append("**")
        # Function/keyword normalization (single-word)
        elif t in {"plus"}:
            normalized.append("+")
        elif t in {"minus"}:
            normalized.append("-")
        elif t in {"times"}:
            normalized.append("*")
        elif t == "multiplied" and i + 1 < len(tokens) and tokens[i+1] == "by":
            normalized.append("*")
            i += 1  # Skip 'by'
        elif t == "divided" and i + 1 < len(tokens) and tokens[i+1] == "by":
            normalized.append("/")
            i += 1
        elif t == "over":
            normalized.append("/")
        elif t == "to" and i+3 < len(tokens) and tokens[i+1] == "the" and tokens[i+2] == "power" and tokens[i+3] == "of":
            normalized.append("**")
            i += 3
        elif t == "infinity":
            normalized.append("oo")
        elif t == "arcsin":
            normalized.append("asin")
        elif t == "arccos":
            normalized.append("acos")
        elif t == "arctan":
            normalized.append("atan")
        elif t == "ln":
            normalized.append("log")
        elif t == "matrix":
            normalized.append("Matrix")
        elif t == "determinant":
            normalized.append("det")
        elif t == "det":
            normalized.append("det")
        elif t == "inverse":
            normalized.append("inv")
        elif t == "transpose":
            normalized.append("transpose")
        elif t == "rank":
            normalized.append("rank")
        elif t == "eigenvalues" or t == "eigenvalue":
            normalized.append("eigenvals")
        elif t == "eigenvectors" or t == "eigenvector":
            normalized.append("eigenvects")
        elif t == "adjoint":
            normalized.append("adjugate")
        # Remove leading command keywords
        elif i == 0 and t in {
            "solve", "calculate", "compute", "evaluate", "find", "answer",
            "what", "differentiate", "derivative", "integrate", "integral", "limit",
            "expand", "factor", "factorize", "factorise", "simplify"
        }:
            # skip
            pass
        # Remove 'is' after 'what'
        elif i > 0 and tokens[i-1] == "what" and t == "is":
            pass
        # Remove 'as', 'when'
        elif t in {"as", "when"}:
            pass
        # Replace 'approaches', 'tends to'
        elif t == "approaches":
            normalized.append("->")
        elif t == "tends" and i+1 < len(tokens) and tokens[i+1] == "to":
            normalized.append("->")
            i += 1
        # Remove 'lim' at start
        elif i == 0 and t == "lim":
            pass
        else:
            normalized.append(t)
        i += 1
    # Handle "square root of" and "cube root of" and "squared"/"cubed"
    i = 0
    result = []
    while i < len(normalized):
        t = normalized[i]
        # square root of x
        if (
            t == "square"
            and i + 2 < len(normalized)
            and normalized[i + 1] == "root"
            and normalized[i + 2] == "of"
        ):
            if i + 3 < len(normalized):
                result.append(f"sqrt({normalized[i+3]})")
                i += 4
                continue
        # cube root of x
        if (
            t == "cube"
            and i + 2 < len(normalized)
            and normalized[i + 1] == "root"
            and normalized[i + 2] == "of"
        ):
            if i + 3 < len(normalized):
                result.append(f"cbrt({normalized[i+3]})")
                i += 4
                continue
        # x squared
        if (
            i + 1 < len(normalized)
            and normalized[i + 1] == "squared"
            and re.match(r"^[a-zA-Z]\w*$", t)
        ):
            result.append(f"{t}**2")
            i += 2
            continue
        # x cubed
        if (
            i + 1 < len(normalized)
            and normalized[i + 1] == "cubed"
            and re.match(r"^[a-zA-Z]\w*$", t)
        ):
            result.append(f"{t}**3")
            i += 2
            continue
        # sin x -> sin(x)
        if (
            t in {"sin", "cos", "tan", "log", "sqrt", "sec", "cosec", "cot", "csc", "abs", "exp"}
            and i + 1 < len(normalized)
            and re.match(r"^[a-zA-Z0-9_()+\-/*]+$", normalized[i + 1])
        ):
            # Only add parentheses if not already present
            arg = normalized[i + 1]
            if not arg.startswith("("):
                fname = t
                if fname == "abs":
                    fname = "Abs"
                result.append(f"{fname}({arg})")
                i += 2
                continue
        result.append(t)
        i += 1
    return result

def _reconstruct_expression(tokens: list[str]) -> str:
    """
    Join tokens back into a math expression string, removing spaces except around '=' and ','.
    """
    # Remove spaces except for = and ,
    expr = ""
    for i, t in enumerate(tokens):
        if t in {"=", ","}:
            expr += f" {t} "
        else:
            expr += t
    # Remove double spaces
    expr = re.sub(r"\s+", " ", expr)
    # Remove spaces around operators except = and ,
    expr = re.sub(r"\s*([+\-*/^(){}\[\]])\s*", r"\1", expr)
    expr = expr.strip()
    return expr

def _clean_expression(question: str):
    """
    Cleans and preprocesses the input mathematical expression string.
    """
    tokens = _tokenize_math_input(question)
    tokens = _normalize_tokens(tokens)
    expr = _reconstruct_expression(tokens)

    # Keep the remaining parsing-specific cleanup already present
    expr = re.sub(
        r"^lim", "", expr
    )
    expr = re.sub(r"\bas\b", "", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bapproaches\b", "->", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\btends\s+to\b", "->", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bwhen\b", "", expr, flags=re.IGNORECASE)

    # Remove trailing limit specification so only the expression remains
    expr = re.sub(
        r"[a-zA-Z]+\s*(?:->|→)\s*[-+]?\d+(?:\.\d+)?",
        "",
        expr,
    )
    expr = re.sub(r"\bdet\b", "det", expr)
    expr = re.sub(r"\binverse\b", "inv", expr)
    expr = re.sub(r"\btranspose\b", "transpose", expr)
    expr = re.sub(r"\bdeterminant\b", "det", expr)
    expr = re.sub(r"\brank\b", "rank", expr)
    expr = re.sub(r"\beigenvalues\b", "eigenvals", expr)
    expr = re.sub(r"\beigenvalue\b", "eigenvals", expr)
    expr = re.sub(r"\beigenvectors\b", "eigenvects", expr)
    expr = re.sub(r"\beigenvector\b", "eigenvects", expr)
    expr = re.sub(r"\badjoint\b", "adjugate", expr)
    return expr.strip()

def _format_sympy_answer(title: str, body: str) -> str:
    return (
        f"📘 {title}\n"
        f"{'=' * (len(title) + 2)}\n\n"
        f"{body.strip()}\n"
    )

# --- Educational step-formatting helpers ---

def _format_derivative_steps(variable, result):
    body = (
        f"Step 1: Take the derivative with respect to {variable}.\n\n"
        f"Derivative:\n{result}\n\n"
        f"Final Answer: {result}"
    )
    return _format_sympy_answer("Derivative", body)

def _format_integral_steps(variable, result):
    body = (
        f"Step 1: Integrate with respect to {variable}.\n\n"
        f"Integral:\n{result} + C\n\n"
        f"Final Answer: {result} + C"
    )
    return _format_sympy_answer("Integral", body)

def _format_limit_steps(variable, point, result):
    body = (
        f"Step 1: Take the limit as {variable} approaches {point}.\n\n"
        f"Limit:\n{result}\n\n"
        f"Final Answer: {result}"
    )
    return _format_sympy_answer("Limit", body)

def _format_expand_steps(result):
    body = (
        f"Step 1: Expand the expression.\n\n"
        f"Expanded:\n{result}\n\n"
        f"Final Answer: {result}"
    )
    return _format_sympy_answer("Expanded", body)

def _format_factor_steps(result):
    body = (
        f"Step 1: Factor the expression.\n\n"
        f"Factored:\n{result}\n\n"
        f"Final Answer: {result}"
    )
    return _format_sympy_answer("Factored", body)

def _format_equation_steps(solution_body):
    body = (
        f"Step 1: Rearrange and solve the equation.\n\n"
        f"{solution_body}\n\n"
        f"Final Answer:\n{solution_body}"
    )
    return _format_sympy_answer("Solution", body)

# ---- Additional step-formatting helpers (NCERT-style) ----
def _format_polynomial_derivative_steps(variable, expression, result):
    body = (
        f"Step 1: Identify the polynomial expression in {variable}: {expression}\n\n"
        f"Step 2: Differentiate each term with respect to {variable}.\n\n"
        f"Final Answer: {result}"
    )
    return _format_sympy_answer("Polynomial Derivative", body)

def _format_trigonometric_derivative_steps(variable, expression, result):
    body = (
        f"Step 1: Identify the trigonometric function(s) in {variable}: {expression}\n\n"
        f"Step 2: Apply the differentiation rules for trigonometric functions.\n\n"
        f"Final Answer: {result}"
    )
    return _format_sympy_answer("Trigonometric Derivative", body)

def _format_exponential_derivative_steps(variable, expression, result):
    body = (
        f"Step 1: Identify the exponential function(s) in {variable}: {expression}\n\n"
        f"Step 2: Apply the differentiation rules for exponential functions.\n\n"
        f"Final Answer: {result}"
    )
    return _format_sympy_answer("Exponential Derivative", body)

def _format_logarithmic_derivative_steps(variable, expression, result):
    body = (
        f"Step 1: Identify the logarithmic function(s) in {variable}: {expression}\n\n"
        f"Step 2: Apply the differentiation rules for logarithmic functions.\n\n"
        f"Final Answer: {result}"
    )
    return _format_sympy_answer("Logarithmic Derivative", body)

def _format_polynomial_integral_steps(variable, expression, result):
    body = (
        f"Step 1: Identify the polynomial expression in {variable}: {expression}\n\n"
        f"Step 2: Integrate each term with respect to {variable}.\n\n"
        f"Final Answer: {result} + C"
    )
    return _format_sympy_answer("Polynomial Integral", body)

def _format_trigonometric_integral_steps(variable, expression, result):
    body = (
        f"Step 1: Identify the trigonometric function(s) in {variable}: {expression}\n\n"
        f"Step 2: Apply the integration rules for trigonometric functions.\n\n"
        f"Final Answer: {result} + C"
    )
    return _format_sympy_answer("Trigonometric Integral", body)

def _format_exponential_integral_steps(variable, expression, result):
    body = (
        f"Step 1: Identify the exponential function(s) in {variable}: {expression}\n\n"
        f"Step 2: Apply the integration rules for exponential functions.\n\n"
        f"Final Answer: {result} + C"
    )
    return _format_sympy_answer("Exponential Integral", body)

def _format_linear_equation_steps(solution_body):
    body = (
        f"Step 1: Identify the linear equation and collect like terms.\n\n"
        f"Step 2: Isolate the variable to solve.\n\n"
        f"Final Answer: {solution_body}"
    )
    return _format_sympy_answer("Linear Equation Solution", body)

def _format_quadratic_equation_steps(solution_body):
    body = (
        f"Step 1: Identify the quadratic equation and bring all terms to one side.\n\n"
        f"Step 2: Apply the quadratic formula or factorization to solve.\n\n"
        f"Final Answer: {solution_body}"
    )
    return _format_sympy_answer("Quadratic Equation Solution", body)

def _format_determinant_steps(matrix, result):
    body = (
        f"Step 1: Write the matrix:\n{matrix}\n\n"
        f"Step 2: Compute the determinant using expansion or row operations.\n\n"
        f"Final Answer: {result}"
    )
    return _format_sympy_answer("Determinant", body)

def _format_inverse_steps(matrix, result):
    body = (
        f"Step 1: Write the matrix:\n{matrix}\n\n"
        f"Step 2: Compute the inverse using adjoint and determinant or row reduction.\n\n"
        f"Final Answer:\n{result}"
    )
    return _format_sympy_answer("Inverse Matrix", body)

def _format_transpose_steps(matrix, result):
    body = (
        f"Step 1: Write the matrix:\n{matrix}\n\n"
        f"Step 2: Interchange rows and columns to get the transpose.\n\n"
        f"Final Answer:\n{result}"
    )
    return _format_sympy_answer("Transpose", body)

def _format_rank_steps(matrix, result):
    body = (
        f"Step 1: Write the matrix:\n{matrix}\n\n"
        f"Step 2: Reduce the matrix to row echelon form to count non-zero rows.\n\n"
        f"Final Answer: {result}"
    )
    return _format_sympy_answer("Rank", body)

def _format_eigenvalue_steps(matrix, result):
    body = (
        f"Step 1: Write the matrix:\n{matrix}\n\n"
        f"Step 2: Find the characteristic equation and solve for eigenvalues.\n\n"
        f"Final Answer:\n{result}"
    )
    return _format_sympy_answer("Eigenvalues", body)

def _format_eigenvector_steps(matrix, result):
    body = (
        f"Step 1: Write the matrix:\n{matrix}\n\n"
        f"Step 2: For each eigenvalue, solve (A - λI)x = 0 to get eigenvectors.\n\n"
        f"Final Answer:\n{result}"
    )
    return _format_sympy_answer("Eigenvectors", body)

# ---- Dispatcher for step formatting ----
def _generate_solution_steps(expr, category, result, **kwargs):
    if category == MathCategory.DERIVATIVE:
        variable = kwargs.get("variable", "x")
        # Product rule: expr is Mul
        if getattr(expr, "is_Mul", False):
            return _apply_product_rule_steps(expr, variable, result)
        # Quotient rule: contains division or negative exponent
        expr_str = str(expr)
        has_div = "/" in expr_str
        has_neg_pow = any(
            isinstance(arg, sp.Pow) and getattr(arg, "exp", 0) < 0
            for arg in getattr(expr, "args", [])
        )
        if has_div or has_neg_pow:
            return _apply_quotient_rule_steps(expr, variable, result)
        # Chain rule: nested functions with nontrivial arguments
        if expr.has(sp.sin, sp.cos, sp.tan, sp.exp, sp.log):
            # Check for nested (argument not a symbol)
            for func in [sp.sin, sp.cos, sp.tan, sp.exp, sp.log]:
                for sub in expr.atoms(func):
                    args = getattr(sub, "args", ())
                    if args and not (len(args) == 1 and args[0].is_Symbol):
                        return _apply_chain_rule_steps(expr, variable, result)
        # Default: power rule/termwise diff
        return _apply_power_rule_steps(expr, variable, result)

    if category == MathCategory.INTEGRAL:
        expr_text = str(expr)
        variable = kwargs.get("variable", "x")
        if any(f in expr_text for f in ["sin", "cos", "tan", "sec", "csc", "cot"]):
            return _format_trigonometric_integral_steps(variable, expr, result)
        if "exp" in expr_text:
            return _format_exponential_integral_steps(variable, expr, result)
        return _format_polynomial_integral_steps(variable, expr, result)

    if category == MathCategory.EXPANSION:
        return _apply_binomial_expansion_steps(expr, result)
    if category == MathCategory.FACTORIZATION:
        return _apply_factorization_steps(expr, result)
    return _format_sympy_answer("Result", str(result))

# --- Lightweight builder helpers for step text ---
def _build_polynomial_steps(expr):
    # Returns a list of step strings for a polynomial expression
    terms = list(sp.Add.make_args(expr))
    steps = []
    steps.append("Identify the polynomial terms:")
    for term in terms:
        steps.append(f"  - {sp.pretty(term)}")
    steps.append("Apply the appropriate rule to each term.")
    return steps

def _build_trigonometric_steps(expr):
    # Returns a list of step strings listing trigonometric functions found in expr
    trig_funcs = [sp.sin, sp.cos, sp.tan, sp.sec, sp.csc, sp.cot]
    found = []
    for func in trig_funcs:
        found += list(expr.atoms(func))
    steps = []
    if found:
        steps.append("Identify the trigonometric function(s) present:")
        for f in found:
            steps.append(f"  - {sp.pretty(f)}")
    else:
        steps.append("No trigonometric functions detected.")
    steps.append("Apply the respective trigonometric rule to each function.")
    return steps

def _build_exponential_steps(expr):
    # Returns a list of step strings for exponential terms in expr
    steps = []
    if expr.has(sp.exp):
        exp_terms = list(expr.atoms(sp.exp))
        steps.append("Identify the exponential function(s) present:")
        for f in exp_terms:
            steps.append(f"  - {sp.pretty(f)}")
        steps.append("Apply the rules for exponential expressions.")
    else:
        steps.append("No exponential terms detected.")
    return steps

def _build_logarithmic_steps(expr):
    # Returns a list of step strings for logarithmic terms in expr
    steps = []
    if expr.has(sp.log):
        log_terms = list(expr.atoms(sp.log))
        steps.append("Identify the logarithmic function(s) present:")
        for f in log_terms:
            steps.append(f"  - {sp.pretty(f)}")
        steps.append("Apply the rules for logarithmic expressions.")
    else:
        steps.append("No logarithmic terms detected.")
    return steps

def _build_matrix_steps(matrix, operation):
    # Returns a list of step strings for the specified matrix operation
    steps = []
    steps.append(f"Write the matrix:\n{matrix}")
    if operation == "determinant":
        steps.append("Compute the determinant using expansion or row operations.")
    elif operation == "inverse":
        steps.append("Compute the inverse using adjoint and determinant or row reduction.")
    elif operation == "transpose":
        steps.append("Interchange rows and columns to get the transpose.")
    elif operation == "rank":
        steps.append("Reduce the matrix to row echelon form to count non-zero rows.")
    elif operation == "eigenvalues":
        steps.append("Find the characteristic equation and solve for eigenvalues.")
    elif operation == "eigenvectors":
        steps.append("For each eigenvalue, solve (A - λI)x = 0 to get eigenvectors.")
    else:
        steps.append("Perform the specified matrix operation.")
    return steps

def _build_equation_steps(lhs, rhs):
    # Returns a list of step strings for solving an equation
    steps = []
    steps.append(f"Given equation: {sp.pretty(lhs)} = {sp.pretty(rhs)}")
    steps.append("Rearrange the equation to bring all terms to one side.")
    steps.append("Isolate the variable and solve for its value.")
    return steps

def _build_limit_steps(expr, variable, point):
    # Returns a list of step strings for evaluating a limit
    steps = []
    steps.append(f"Take the limit as {variable} approaches {point}.")
    steps.append(f"Substitute the value of {variable} into the expression as it approaches {point}.")
    steps.append("Simplify to get the final value of the limit.")
    return steps

def _build_factorization_steps(expr):
    # Returns a list of step strings for factorization
    steps = []
    steps.append("Identify common factors or use algebraic identities.")
    steps.append("Write the expression as a product of its factors.")
    return steps

def _build_expansion_steps(expr):
    # Returns a list of step strings for expansion
    steps = []
    steps.append("Recognize the expression as a binomial or polynomial to be expanded.")
    steps.append("Expand using the Binomial Theorem or distributive property.")
    return steps

# --- Custom NCERT-style step helpers for rules/operations ---
def _apply_power_rule_steps(expression, variable, result):
    # Use _build_polynomial_steps for step text
    steps = _build_polynomial_steps(expression)
    steps.append(f"Final Answer: {result}")
    body = "\n\n".join(steps)
    return _format_sympy_answer("Power Rule Derivative", body)

def _apply_product_rule_steps(expression, variable, result):
    steps = [
        "Recognize the expression as a product of two or more functions.",
        "Apply the product rule: d/dx[u*v] = u'*v + u*v'.",
        f"Final Answer: {result}",
    ]
    body = "\n\n".join(steps)
    return _format_sympy_answer("Product Rule Derivative", body)

def _apply_quotient_rule_steps(expression, variable, result):
    steps = [
        "Recognize the expression as a quotient of two functions.",
        "Apply the quotient rule: d/dx[u/v] = (u'*v - u*v')/v^2.",
        f"Final Answer: {result}",
    ]
    body = "\n\n".join(steps)
    return _format_sympy_answer("Quotient Rule Derivative", body)

def _apply_chain_rule_steps(expression, variable, result):
    steps = [
        "Recognize the expression as a composition of functions.",
        "Apply the chain rule: d/dx[f(g(x))] = f'(g(x))*g'(x).",
        f"Final Answer: {result}",
    ]
    body = "\n\n".join(steps)
    return _format_sympy_answer("Chain Rule Derivative", body)

def _apply_linear_equation_steps(solution_body):
    steps = [
        "Bring all terms of the linear equation to one side and collect like terms.",
        "Isolate the variable and solve for its value.",
        f"Final Answer: {solution_body}",
    ]
    body = "\n\n".join(steps)
    return _format_sympy_answer("Linear Equation Solution", body)

def _apply_quadratic_formula_steps(solution_body):
    steps = [
        "Bring all terms of the quadratic equation to one side (ax^2 + bx + c = 0).",
        "Apply the quadratic formula: x = [-b ± sqrt(b^2 - 4ac)]/(2a).",
        f"Final Answer: {solution_body}",
    ]
    body = "\n\n".join(steps)
    return _format_sympy_answer("Quadratic Equation Solution", body)

def _apply_factorization_steps(expression, result):
    steps = _build_factorization_steps(expression)
    steps.append(f"Final Answer: {result}")
    body = "\n\n".join(steps)
    return _format_sympy_answer("Factorization", body)

def _apply_binomial_expansion_steps(expression, result):
    steps = _build_expansion_steps(expression)
    steps.append(f"Final Answer: {result}")
    body = "\n\n".join(steps)
    return _format_sympy_answer("Binomial Expansion", body)

def _apply_matrix_determinant_steps(matrix, result):
    steps = _build_matrix_steps(matrix, "determinant")
    steps.append(f"Final Answer: {result}")
    body = "\n\n".join(steps)
    return _format_sympy_answer("Determinant", body)

def _apply_matrix_inverse_steps(matrix, result):
    steps = _build_matrix_steps(matrix, "inverse")
    steps.append(f"Final Answer:\n{result}")
    body = "\n\n".join(steps)
    return _format_sympy_answer("Inverse Matrix", body)
def _solve_matrix(question: str):
    try:
        import ast
        # Find the first [[...]] matrix literal
        match = re.search(r"\[\s*\[.*?\]\s*(?:,\s*\[.*?\]\s*)*\]", question.replace('\n',' '), re.DOTALL)
        if not match:
            raise ValueError("No matrix found in question.")
        matrix_literal = match.group(0)
        matrix_data = ast.literal_eval(matrix_literal)
        matrix = sp.Matrix(matrix_data)
        if not matrix.is_Matrix:
            raise ValueError("Invalid matrix.")
        if matrix.rows == 0 or matrix.cols == 0:
            raise ValueError("Empty matrix.")
        q_lower = question.casefold()
        q_lower = q_lower.replace("eigenvals", "eigenvalues")
        q_lower = q_lower.replace("eigenvects", "eigenvectors")
        # Determine operation
        if re.search(r"\b(det|determinant)\b", q_lower):
            result = matrix.det()
            answer = _apply_matrix_determinant_steps(matrix, result)
        elif re.search(r"\b(inv|inverse)\b", q_lower):
            if matrix.det() == 0:
                raise ValueError("Matrix is singular and has no inverse.")
            result = matrix.inv()
            answer = _apply_matrix_inverse_steps(matrix, result)
        elif re.search(r"\btranspose\b", q_lower):
            result = matrix.T
            answer = _format_transpose_steps(matrix, result)
        elif re.search(r"\brank\b", q_lower):
            result = matrix.rank()
            answer = _format_rank_steps(matrix, result)
        elif re.search(r"\beigenvalues?\b", q_lower):
            result = matrix.eigenvals()
            answer = _format_eigenvalue_steps(matrix, result)
        elif re.search(r"\beigenvectors?\b", q_lower):
            result = matrix.eigenvects()
            answer = _format_eigenvector_steps(matrix, result)
        else:
            result = matrix
            answer = _format_sympy_answer("Matrix", str(result))
        return {"answer": answer, "verified": True, "source": "sympy"}
    except Exception as e:
        return {"answer": f"Matrix error: {e}", "verified": False, "source": "sympy"}

def _solve_with_sympy(question: str):
    expr_str = _clean_expression(question)
    category = classify_math_question(question)
    local_dict = {
        "x": sp.Symbol("x"),
        "y": sp.Symbol("y"),
        "z": sp.Symbol("z"),
        "pi": sp.pi,
        "e": sp.E,
        "sin": sp.sin,
        "cos": sp.cos,
        "tan": sp.tan,
        "log": sp.log,
        "sqrt": sp.sqrt,
        "asin": sp.asin,
        "acos": sp.acos,
        "atan": sp.atan,
        "abs": sp.Abs,
        "sec": sp.sec,
        "cosec": sp.csc,
        "csc": sp.csc,
        "cot": sp.cot,
        "sinh": sp.sinh,
        "cosh": sp.cosh,
        "tanh": sp.tanh,
        "exp": sp.exp,
        "Abs": sp.Abs,
        "Matrix": sp.Matrix,
        "GoldenRatio": sp.GoldenRatio,
        "oo": sp.oo,
        "cbrt": lambda x: x ** sp.Rational(1, 3),
    }
    try:
        # Try to parse as an equation if '=' present
        if '=' in expr_str and '==' not in expr_str:
            parts = expr_str.split("=", 1)
            if len(parts) != 2:
                raise ValueError("Invalid equation")
            lhs, rhs = parts
            lhs_expr = parse_expr(lhs, local_dict=local_dict)
            rhs_expr = parse_expr(rhs, local_dict=local_dict)
            eq = sp.Eq(lhs_expr, rhs_expr)
            variables = sorted(eq.free_symbols, key=lambda s: s.name)
            sol = (
                sp.solve(eq, list(variables), dict=True)
                if variables
                else sp.solve(eq)
            )
            if isinstance(sol, dict):
                sol = [sol]
            # Format solution line by line if list of dicts
            if isinstance(sol, list) and sol and all(isinstance(item, dict) for item in sol):
                lines = []
                for d in sol:
                    for k, v in d.items():
                        lines.append(f"{k} = {v}")
                body = "\n".join(lines) if lines else str(sol)
            else:
                body = str(sol)
            # Use quadratic or linear formatting depending on degree
            try:
                deg = sp.degree(lhs_expr - rhs_expr)
            except Exception:
                deg = None
            if deg == 2:
                answer = _apply_quadratic_formula_steps(body)
            else:
                answer = _apply_linear_equation_steps(body)
        else:
            # Try to parse expression
            expr = parse_expr(expr_str, local_dict=local_dict)
            # Try simplification
            simplified = sp.simplify(expr)
            if category == MathCategory.SIMPLIFICATION:
                body = f"Step 1: Simplify the expression.\n\nFinal Answer: {simplified}"
                answer = _format_sympy_answer("Simplified", body)
            else:
                # Try derivative if category is DERIVATIVE
                if category == MathCategory.DERIVATIVE:
                    variables = sorted(expr.free_symbols, key=lambda s: s.name)
                    x = variables[0] if variables else sp.Symbol('x')
                    deriv = sp.diff(expr, x)
                    answer = _generate_solution_steps(expr, category, deriv, variable=x)
                # Try integral if category is INTEGRAL
                elif category == MathCategory.INTEGRAL:
                    variables = sorted(expr.free_symbols, key=lambda s: s.name)
                    x = variables[0] if variables else sp.Symbol('x')
                    integ = sp.integrate(expr, x)
                    answer = _generate_solution_steps(expr, category, integ, variable=x)
                # Try limit if category is LIMIT
                elif category == MathCategory.LIMIT:
                    variables = sorted(expr.free_symbols, key=lambda s: s.name)
                    x = variables[0] if variables else sp.Symbol('x')
                    match = re.search(
                        r"[a-zA-Z]+\s*(?:->|→|to|approaches)\s*([-+]?\d+(?:\.\d+)?)",
                        question,
                        re.IGNORECASE,
                    )
                    direction = "+"
                    if re.search(r"\bleft\b", question, re.IGNORECASE):
                        direction = "-"
                    elif re.search(r"\bright\b", question, re.IGNORECASE):
                        direction = "+"
                    if match:
                        lim = sp.limit(expr, x, sp.Float(match.group(1)), dir=direction)
                    elif re.search(r"\binf(inity)?\b|∞", question, re.IGNORECASE):
                        lim = sp.limit(expr, x, sp.oo)
                    else:
                        lim = sp.limit(expr, x, 0)
                    answer = _format_limit_steps(x, match.group(1) if match else "0", lim)
                # Try expand if category is EXPANSION
                elif category == MathCategory.EXPANSION:
                    expanded = sp.expand(expr)
                    answer = _generate_solution_steps(expr, category, expanded)
                # Try factor if category is FACTORIZATION
                elif category == MathCategory.FACTORIZATION:
                    factored = sp.factor(expr)
                    answer = _generate_solution_steps(expr, category, factored)
                elif category == MathCategory.MATRIX:
                    return _solve_matrix(expr_str if "[[" in expr_str else question)
                elif category == MathCategory.BINOMIAL:
                    answer = _format_sympy_answer("Expanded", str(sp.expand(expr)))
                elif category == MathCategory.INEQUALITY:
                    answer = "Inequality solving is not yet supported by the SymPy pipeline."
                elif category == MathCategory.FUNCTION:
                    answer = "Function analysis is handled by the LLM."
                elif category == MathCategory.SEQUENCE_SERIES:
                    answer = "Sequence/series reasoning is handled by the LLM."
                elif category == MathCategory.DIFFERENTIAL_EQUATION:
                    try:
                        variables = sorted(expr.free_symbols, key=lambda s: s.name) if "expr" in locals() else []
                        x = variables[0] if variables else sp.Symbol("x")
                        y = sp.Function("y")
                        locals_dict = dict(local_dict)
                        locals_dict.update({"x": x, "y": y})
                        equation = sp.sympify(expr_str, locals=locals_dict)
                        answer = _format_sympy_answer("Differential Equation", str(sp.dsolve(equation)))
                    except Exception:
                        answer = "Differential equation solving is handled by the LLM."
                elif category == MathCategory.VECTOR_3D:
                    answer = "3D vector problems are handled by the LLM unless they reduce to symbolic expressions."
                elif category == MathCategory.CONIC_SECTION:
                    answer = "Conic section analysis is handled by the LLM unless symbolic expansion is required."
                elif category == MathCategory.RELATION:
                    answer = "Relation problems are handled by the LLM."
                elif category == MathCategory.BOOLEAN_LOGIC:
                    answer = "Boolean logic problems are handled by the LLM."
                else:
                    numeric = sp.N(sp.simplify(expr))
                    if numeric.is_number:
                        if getattr(numeric, "is_real", False) and bool(numeric.is_integer):
                            answer = _format_sympy_answer("Result", str(int(numeric)))
                        else:
                            # Strip trailing zeros from decimal output before formatting
                            num_str = str(sp.N(numeric, 10))
                            if "." in num_str:
                                num_str = num_str.rstrip("0").rstrip(".") if "." in num_str else num_str
                            answer = _format_sympy_answer("Result", num_str)
                    else:
                        answer = _format_sympy_answer("Result", str(expr))
        placeholder_prefixes = (
            "Function analysis",
            "Sequence/series",
            "Relation problems",
            "Boolean logic",
            "3D vector",
            "Conic section",
            "Inequality solving",
            "Differential equation solving",
            "Matrix operations",
            "Vector",
            "Matrix",
            "handled by the LLM",
            "LLM.",
            "require structured matrix",
            "not yet supported",
            "handled by the dedicated",
            "require structured",
        )
        if any(str(answer).startswith(p) for p in placeholder_prefixes):
            return {"answer": str(answer), "verified": False, "source": "sympy"}
        return {"answer": str(answer), "verified": True, "source": "sympy"}
    except Exception as e:
        return {"answer": f"Sympy error: {str(e)}", "verified": False, "source": "sympy"}

async def _sympy_task(question: str):
    loop = asyncio.get_running_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(SYMPY_EXECUTOR, _solve_with_sympy, question),
            timeout=3,
        )
        return result
    except asyncio.TimeoutError:
        return {"answer": "Sympy solver timed out", "verified": False, "source": "sympy"}
    except Exception as e:
        return {"answer": f"Sympy error: {e}", "verified": False, "source": "sympy"}

async def _llm_task(question: str):
    prompt = f"Solve the following math problem step-by-step, showing your reasoning, and provide a clearly labeled final answer:\n{question}"
    try:
        response = await asyncio.to_thread(
            client.responses.create,
            model=settings.LLM_MODEL,
            input=prompt,
        )
        answer_text = getattr(response, "output_text", "").strip()
        return {"answer": answer_text, "verified": False, "source": "llm"}
    except Exception as e:
        return {"answer": f"LLM error: {str(e)}", "verified": False, "source": "llm"}

async def solve_math_question(question: str, language: str = "english"):
    category = classify_math_question(question)

    if category in {
        MathCategory.WORD_PROBLEM,
        MathCategory.FUNCTION,
        MathCategory.SEQUENCE_SERIES,
        MathCategory.RELATION,
        MathCategory.BOOLEAN_LOGIC,
    }:
        sympy_result = {
            "answer": "",
            "verified": False,
            "source": "sympy",
        }
        llm_result = await _llm_task(question)
    else:
        sympy_result, llm_result = await asyncio.gather(
            _sympy_task(question),
            _llm_task(question)
        )
    # If sympy answer is verified and not error, use it
    if sympy_result.get("verified") and not sympy_result["answer"].startswith("Sympy error") and not sympy_result["answer"].startswith("Sympy solver timed out"):
        if llm_result.get("answer", "").strip():
            answer = llm_result["answer"].rstrip() + "\n\n━━━━━━━━━━━━━━━━━━\n✅ Verified by SymPy\n\n" + sympy_result["answer"]
        else:
            answer = sympy_result["answer"]
        verified = True
        source = "sympy"
    else:
        answer = llm_result["answer"]
        verified = False
        source = "llm"
    # Translate answer if language is not English
    if language.lower() != "english":
        translated = translate_answer(answer or "", language)
        if translated:
            answer = translated
    return {"answer": answer, "verified": verified, "source": source}