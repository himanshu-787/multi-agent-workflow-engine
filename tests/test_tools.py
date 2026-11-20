import pytest
from app.tools.calculator import CalculatorTool
from app.tools.code_executor import CodeExecutorTool
from app.tools.file_tools import FileReaderTool, FileWriterTool
from app.tools.registry import ToolRegistry, default_registry
from app.tools.search import WebSearchTool


def test_code_executor_success():
    tool = CodeExecutorTool()
    res = tool.run(code="print('Hello from tool!')")
    assert res.success is True
    assert "Hello from tool!" in res.output
    assert res.error is None


def test_code_executor_syntax_error():
    tool = CodeExecutorTool()
    res = tool.run(code="def broken(:\n    pass")
    assert res.success is False
    assert "SyntaxError" in res.error or "exited with code" in res.error


def test_code_executor_timeout():
    tool = CodeExecutorTool()
    res = tool.run(code="import time\ntime.sleep(2)", timeout_seconds=1)
    assert res.success is False
    assert "timed out" in res.error


def test_calculator_arithmetic():
    calc = CalculatorTool()
    res = calc.run(expression="(10 + 5) * 4 - 20 / 2")
    assert res.success is True
    assert float(res.output) == 50.0


def test_calculator_division_by_zero():
    calc = CalculatorTool()
    res = calc.run(expression="10 / 0")
    assert res.success is False
    assert "Division by zero" in res.error


def test_calculator_invalid_syntax():
    calc = CalculatorTool()
    res = calc.run(expression="import os; os.system('ls')")
    assert res.success is False
    assert "Invalid arithmetic expression" in res.error or "Unsupported" in res.error


def test_file_tools_read_write(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    writer = FileWriterTool()
    reader = FileReaderTool()

    write_res = writer.run(file_path="test_file.txt", content="Hello, Multi-Agent!")
    assert write_res.success is True

    read_res = reader.run(file_path="test_file.txt")
    assert read_res.success is True
    assert read_res.output == "Hello, Multi-Agent!"


def test_file_tools_path_traversal(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reader = FileReaderTool()
    res = reader.run(file_path="../../etc/passwd")
    assert res.success is False
    assert "escapes workspace directory" in res.error or "Access denied" in res.error


def test_web_search():
    search = WebSearchTool()
    res = search.run(query="fibonacci sequence", max_results=2)
    assert res.success is True
    assert "Fibonacci" in res.output


def test_tool_registry_validation():
    registry = ToolRegistry()
    assert "code_executor" in registry.list_tools()
    assert "calculator" in registry.list_tools()

    # Valid execution
    res = registry.execute("calculator", expression="2 + 3")
    assert res.success is True
    assert res.output == "5"

    # Schema validation error: missing required 'expression' parameter
    invalid_res = registry.execute("calculator")
    assert invalid_res.success is False
    assert "Validation error" in invalid_res.error

    # Non-existent tool
    missing_res = registry.execute("unknown_tool")
    assert missing_res.success is False
    assert "not registered" in missing_res.error
