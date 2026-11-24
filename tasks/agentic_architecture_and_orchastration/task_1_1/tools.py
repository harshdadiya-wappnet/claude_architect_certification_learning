
from typing import Any

from sympy import (
    symbols,
    sympify,
    Eq,
    solve,
    simplify,
    expand,
    factor,
)
from anthropic.types import ToolParam


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
        expr = sympify(expression)
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
        x = symbols(variable)

        if "=" in equation:
            lhs, rhs = equation.split("=", 1)
            expr = Eq(sympify(lhs), sympify(rhs))
        else:
            expr = sympify(equation)

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


# ==========================================
# 3. TOOL REGISTRY
# ==========================================

tool_registry = {
    "calculate": calculate,
    "solve_equation": solve_equation,
    "solve_quadratic": solve_quadratic
}


# ==========================================
# 4. REGISTERED TOOLS
# ==========================================

tools = [
    calculate_schema,
    solve_equation_schema,
    solve_quadratic_schema
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

    print(f"[Tool Result] {result}\n")

    return result
