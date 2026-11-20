import ast
import operator
from pydantic import BaseModel, Field

from app.tools.base import BaseToolWrapper, ToolResult


class CalculatorInput(BaseModel):
    expression: str = Field(description="Mathematical expression to evaluate, e.g. '(15 * 4) + 12 / 3'")


_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _OPERATORS:
            raise ValueError(f"Unsupported binary operator: {op_type.__name__}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return _OPERATORS[op_type](left, right)
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = _eval_node(node.operand)
        return _OPERATORS[op_type](operand)
    else:
        raise ValueError(f"Unsupported expression element: {type(node).__name__}")


class CalculatorTool(BaseToolWrapper):
    name = "calculator"
    description = "Safely evaluates mathematical arithmetic expressions."
    args_schema = CalculatorInput

    def run(self, expression: str) -> ToolResult:
        try:
            tree = ast.parse(expression.strip(), mode="eval")
            result = _eval_node(tree.body)
            return ToolResult(success=True, output=str(result), error=None)
        except ZeroDivisionError:
            return ToolResult(success=False, output="", error="Division by zero error.")
        except Exception as e:
            return ToolResult(
                success=False, output="", error=f"Invalid arithmetic expression: {str(e)}"
            )
