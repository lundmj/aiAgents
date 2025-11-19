import inspect
from types import UnionType
from typing import Any, Callable, get_type_hints, Literal, get_origin, get_args, Union
import copy

from openai.types.responses import FunctionToolParam


def _is_optional(annotation) -> bool:
    origin = get_origin(annotation)
    args = get_args(annotation)
    return (origin is UnionType or origin is Union) and type(None) in args


def _get_strict_json_schema_type(annotation) -> dict:
    origin = get_origin(annotation)
    args = get_args(annotation)

    if _is_optional(annotation):
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            return _get_strict_json_schema_type(non_none_args[0])
        raise TypeError(f"Unsupported Union with multiple non-None values: {annotation}")

    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
    }

    if annotation in type_map:
        return {"type": type_map[annotation]}

    if origin in type_map:
        return {"type": type_map[origin]}

    if origin is Literal:
        values = args
        if all(isinstance(v, (str, int, bool)) for v in values):
            return {"type": "string" if all(isinstance(v, str) for v in values) else "number", "enum": list(values)}
        raise TypeError("Unsupported Literal values in annotation")

    raise TypeError(f"Unsupported parameter type: {annotation}")


def generate_function_schema(func: Callable[..., Any]) -> FunctionToolParam:
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)

    params = {}
    required = []

    for name, param in sig.parameters.items():
        if name in {"self", "ctx"}:
            continue

        ann = type_hints.get(name, param.annotation)
        if ann is inspect._empty:
            raise TypeError(f"Missing type annotation for parameter: {name}")

        schema_entry = _get_strict_json_schema_type(ann)

        required.append(name)
        params[name] = schema_entry

    return {
        "type": "function",
        "name": func.__name__,
        "description": func.__doc__ or "",
        "parameters": {
            "type": "object",
            "properties": params,
            "required": required,
            "additionalProperties": False
        },
        "strict": True
    }

TOOL_CALL_LOG_DIR = "log"

class ToolBox:
    tools: list[FunctionToolParam]

    def __init__(self):
        self._funcs = {}
        self.tools = []

    def tool(self, func: Callable | None = None, *, name: str | None = None):
        import functools
        import os
        from datetime import datetime

        # support both decorator and direct-call forms
        if func is None:
            return lambda f: self.tool(f, name=name)

        log_path = os.path.join(
            os.path.dirname(__file__),
            TOOL_CALL_LOG_DIR,
            "tool_calls.log"
        )

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry = {
                "timestamp": ts,
                "tool": func.__name__,
                "args": args,
                "kwargs": kwargs,
            }
            try:
                result = func(*args, **kwargs)
                entry["result"] = result
            except Exception as e:
                entry["error"] = str(e)
                log_message = (
                    f"[{entry['timestamp']}] Tool: {entry['tool']}\n"
                    f"  Args: {entry['args']}\n"
                    f"  Kwargs: {entry['kwargs']}\n"
                    f"  Error: {entry['error']}\n"
                    "----------------------------------------\n"
                )
                with open(log_path, "a") as f:
                    f.write(log_message)
                raise
            log_message = (
                f"[{entry['timestamp']}] Tool: {entry['tool']}\n"
                f"  Args: {entry['args']}\n"
                f"  Kwargs: {entry['kwargs']}\n"
                f"  Result: {entry['result']}\n"
                "----------------------------------------\n"
            )
            with open(log_path, "a") as f:
                f.write(log_message)
            return entry.get("result")

        # register under an explicit name if provided, else use the function's name
        reg_name = name or func.__name__
        wrapper.__name__ = reg_name

        self._funcs[reg_name] = wrapper

        # generate schema from original func but override the name so it is unique
        schema = generate_function_schema(func)
        schema["name"] = reg_name
        self.tools.append(copy.deepcopy(schema))

        return wrapper

    def get_tool_function(self, tool_name: str) -> Callable | None:
        return self._funcs.get(tool_name)
    
    def __or__(self, other: "ToolBox | None") -> "ToolBox":
        if other is None:
            return copy.deepcopy(self)
        if not isinstance(other, ToolBox):
            raise TypeError("Operand must be a ToolBox or None")

        merged = ToolBox()
        # start with a shallow copy of left-hand tools and schemas
        for name, wrapper in self._funcs.items():
            merged._funcs[name] = wrapper
        for schema in self.tools:
            merged.tools.append(copy.deepcopy(schema))

        # overlay with right-hand tools (overwrite on conflict)
        for schema in other.tools:
            name = schema["name"]
            merged._funcs[name] = other._funcs[name]
            # remove any existing schema with the same name
            merged.tools = [s for s in merged.tools if s["name"] != name]
            merged.tools.append(copy.deepcopy(schema))

        return merged

    def __ior__(self, other: "ToolBox | None") -> "ToolBox":
        if other is None:
            return self
        merged = self | other
        self._funcs = merged._funcs
        self.tools = merged.tools
        return self
