import asyncio
from typing import Any
import base64
import mimetypes
from pathlib import Path

import re

import sympy
from sympy import (
    symbols,
    Eq,
    solve,
    simplify,
    expand,
    factor,
)
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    convert_xor,
)
from anthropic.types import ToolParam


# ==========================================
# 0. SAFE EXPRESSION PARSING
# ==========================================
# sympify()/parse_expr() ultimately call eval(). Tool input is model-generated
# and can be steered by prompt injection (e.g. from a file read via read_file),
# so we never hand it to eval unfiltered.

MAX_EXPR_LENGTH = 200

# Only these names may appear in an expression besides short variable names.
_ALLOWED_NAMES = {
    "sqrt": sympy.sqrt, "sin": sympy.sin, "cos": sympy.cos, "tan": sympy.tan,
    "asin": sympy.asin, "acos": sympy.acos, "atan": sympy.atan,
    "log": sympy.log, "ln": sympy.log, "exp": sympy.exp, "Abs": sympy.Abs,
    "abs": sympy.Abs, "pi": sympy.pi, "E": sympy.E,
}

_ALLOWED_CHARS = re.compile(r"[0-9a-zA-Z+\-*/^(). ,]+")
_ATTRIBUTE_ACCESS = re.compile(r"\.\s*[A-Za-z_]")
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_VARIABLE_NAME = re.compile(r"[A-Za-z][A-Za-z0-9]?")  # x, y, t, x1, ...


def safe_parse(text: str) -> sympy.Expr:
    """Validate against an allowlist, then parse with a restricted namespace."""
    text = text.strip()

    if not text:
        raise ValueError("Empty expression.")
    if len(text) > MAX_EXPR_LENGTH:
        raise ValueError(f"Expression too long (max {MAX_EXPR_LENGTH} characters).")
    if not _ALLOWED_CHARS.fullmatch(text):
        raise ValueError("Expression contains disallowed characters.")
    if "__" in text or _ATTRIBUTE_ACCESS.search(text):
        raise ValueError("Attribute access is not allowed.")

    for name in _IDENTIFIER.findall(text):
        if name not in _ALLOWED_NAMES and not _VARIABLE_NAME.fullmatch(name):
            raise ValueError(f"Unknown or disallowed name: '{name}'.")

    return parse_expr(
        text,
        local_dict=dict(_ALLOWED_NAMES),
        # Only the constructors sympy's own transformations emit (Integer(2), Symbol('x'), ...)
        global_dict={
            "Integer": sympy.Integer,
            "Float": sympy.Float,
            "Rational": sympy.Rational,
            "Symbol": sympy.Symbol,
        },
        transformations=standard_transformations + (convert_xor,),
    )


def safe_symbol(name: str) -> sympy.Symbol:
    name = name.strip()
    if not _VARIABLE_NAME.fullmatch(name):
        raise ValueError(f"Invalid variable name: '{name}'.")
    return sympy.Symbol(name)


# ==========================================
# 1. TOOL FUNCTIONS
# ==========================================

async def calculate(expression: str) -> str:
    """
    Perform basic arithmetic and simplify mathematical expressions.

    Supports:
    - Addition
    - Subtraction
    - Multiplication
    - Division
    - Algebraic simplification
    """

    try:
        expr = safe_parse(expression)
        result = simplify(expr)

        return str(result)

    except Exception as e:
        return f"Calculation error: {str(e)}"


async def solve_equation(
    equation: str,
    variable: str = "x"
) -> str:
    """
    Solve an algebraic equation for a given variable.

    Examples:
    - 2*x + 5 = 15
    - x**2 - 5*x + 6 = 0
    - 3*x - 9 = 0
    """

    try:
        x = safe_symbol(variable)

        if "=" in equation:
            lhs, rhs = equation.split("=", 1)
            expr = Eq(safe_parse(lhs), safe_parse(rhs))
        else:
            expr = safe_parse(equation)

        result = solve(expr, x)

        return str(result)

    except Exception as e:
        return f"Equation solving error: {str(e)}"


async def solve_quadratic(
    a: float,
    b: float,
    c: float
) -> str:
    """
    Solve a quadratic equation ax² + bx + c = 0.
    """

    try:
        if a == 0:
            raise ValueError("Coefficient 'a' cannot be zero.")

        x = symbols("x")

        equation = a * x**2 + b * x + c

        result = solve(equation, x)

        return str(result)

    except Exception as e:
        return f"Quadratic solving error: {str(e)}"


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
MAX_FILE_BYTES = 10 * 1024 * 1024   # refuse files larger than 10 MB
MAX_TEXT_CHARS = 100_000            # truncate text so one file can't flood the context


async def build_content_block(file_path: str) -> dict:
    """
    Build a Claude API content block (text / image / document) for a file.

    - Images and PDFs are sent base64-encoded so Claude can view them natively.
    - Everything else is treated as text; if it isn't valid UTF-8 it is
      rejected as binary.
    """
    path = Path(file_path).expanduser()

    if not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    size = path.stat().st_size
    if size > MAX_FILE_BYTES:
        raise ValueError(
            f"File too large ({size:,} bytes). Limit is {MAX_FILE_BYTES:,} bytes."
        )

    ext = path.suffix.lower()

    # Images and PDFs: base64 encode off the event loop
    if ext in IMAGE_EXTENSIONS or ext == ".pdf":
        raw_bytes = await asyncio.to_thread(path.read_bytes)
        data = base64.standard_b64encode(raw_bytes).decode("utf-8")

        if ext == ".pdf":
            return {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": data,
                },
            }

        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": mimetypes.guess_type(path)[0] or "image/png",
                "data": data,
            },
        }

    # Everything else: try to read as text
    try:
        text_data = await asyncio.to_thread(path.read_text, encoding="utf-8")
    except UnicodeDecodeError:
        raise ValueError(
            f"Unsupported binary file type: {ext or '(no extension)'}"
        ) from None

    if len(text_data) > MAX_TEXT_CHARS:
        text_data = (
            text_data[:MAX_TEXT_CHARS]
            + f"\n... [truncated, file has {len(text_data):,} characters]"
        )

    return {
        "type": "text",
        "text": f"--- File: {path.name} ---\n{text_data}",
    }


async def read_file(file_path: str) -> list[dict]:
    """
    Read any file and return its content as a list of content blocks,
    suitable for use as a tool_result's `content`.
    """
    try:
        return [await build_content_block(file_path)]
    except Exception as e:
        return [{"type": "text", "text": f"File read error: {str(e)}"}]


# ==========================================
# 2. TOOL SCHEMAS
# ==========================================

calculate_schema: ToolParam = ToolParam({
    "name": "calculate",
    "description": (
        "Perform mathematical calculations including addition, "
        "subtraction, multiplication, division, and algebraic "
        "expression simplification."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": (
                    "Mathematical expression to calculate. "
                    "Examples: 10*5, 100/5, 2+5*3, 2*x + 5*x"
                )
            }
        },
        "required": ["expression"]
    }
})


solve_equation_schema: ToolParam = ToolParam({
    "name": "solve_equation",
    "description": (
        "Solve algebraic equations for a given variable. "
        "Supports linear, quadratic, and other symbolic equations."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "equation": {
                "type": "string",
                "description": (
                    "Mathematical equation. "
                    "Example: 2*x + 5 = 15"
                )
            },
            "variable": {
                "type": "string",
                "description": "Variable to solve for. Default is x."
            }
        },
        "required": ["equation"]
    }
})


solve_quadratic_schema: ToolParam = ToolParam({
    "name": "solve_quadratic",
    "description": (
        "Solve a quadratic equation in the form ax² + bx + c = 0 "
        "using coefficients a, b, and c."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "a": {
                "type": "number",
                "description": "Coefficient of x squared."
            },
            "b": {
                "type": "number",
                "description": "Coefficient of x."
            },
            "c": {
                "type": "number",
                "description": "Constant coefficient."
            }
        },
        "required": ["a", "b", "c"]
    }
})


read_file_schema: ToolParam = ToolParam({
    "name": "read_file",
    "description": (
        "Read the contents of a file from disk. Supports text files "
        "(.txt, .md, .csv, .json, .py, code, config, etc.), images "
        "(.png, .jpg, .jpeg, .gif, .webp) and PDFs. Returns an error "
        "message for missing, oversized, or unsupported binary files."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": (
                    "Path to the file to read. "
                    "Examples: ./notes.txt, ~/docs/report.pdf, data/chart.png"
                )
            }
        },
        "required": ["file_path"]
    }
})


# ==========================================
# 3. TOOL REGISTRY
# ==========================================

tool_registry = {
    "calculate": calculate,
    "solve_equation": solve_equation,
    "solve_quadratic": solve_quadratic,
    "read_file": read_file
}


# ==========================================
# 4. REGISTERED TOOLS
# ==========================================

tools = [
    calculate_schema,
    solve_equation_schema,
    solve_quadratic_schema,
    read_file_schema
]


# ==========================================
# 5. TOOL EXECUTION
# ==========================================

async def tool_execute(
    tool_name: str,
    tool_input: dict[str, Any]
) -> Any:

    print(f"\n[Tool Call] {tool_name}")
    print(f"[Tool Input] {tool_input}")

    tool_function = tool_registry.get(tool_name)

    if not tool_function:
        raise ValueError(f"Unknown tool: {tool_name}")

    result = await tool_function(**tool_input)

    # Keep logs readable: never dump base64 payloads or whole files to the console
    preview = str(result)
    print(f"[Tool Result] {preview[:300]}{'...' if len(preview) > 300 else ''}\n")

    return result
