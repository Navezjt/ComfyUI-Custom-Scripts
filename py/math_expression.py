import ast
import math
import random
import operator as op

operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Pow: op.pow,
    ast.BitXor: op.xor,
    ast.USub: op.neg,
    ast.Mod: op.mod
}

functions = {
    "round": {
        "args": (1, 2),
        "call": lambda a, b = None: round(a, b)
    },
    "ceil": {
        "args": (1, 1),
        "call": lambda a: math.ceil(a)
    },
    "floor": {
        "args": (1, 1),
        "call": lambda a: math.floor(a)
    },
    "randomint": {
        "args": (2, 2),
        "call": lambda a, b: random.randint(a, b)
    }
}


class MathExpression:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "expression": ("STRING", {"multiline": True, "dynamicPrompts": False}),
            },
            "optional": {
                "a": ("FLOAT", {"forceInput": True}),
                "b": ("FLOAT", {"forceInput": True}),
                "c": ("FLOAT", {"forceInput": True}),
            },
            "hidden": {"extra_pnginfo": "EXTRA_PNGINFO",
                       "prompt": "PROMPT"},
        }

    RETURN_TYPES = ("INT", "FLOAT", "STRING", )
    FUNCTION = "evaluate"
    CATEGORY = "utils"

    
    @classmethod
    def IS_CHANGED(s, expression, **kwargs):
        if "random" in expression:
            return float("nan")
        return expression


    def get_widget_value(self, extra_pnginfo, prompt, node_name, widget_name):
        workflow = extra_pnginfo["workflow"]
        node_id = None
        for node in workflow["nodes"]:
            name = node["type"]
            if "properties" in node:
                if "Node name for S&R" in node["properties"]:
                    name = node["properties"]["Node name for S&R"]
            if name == node_name:
                node_id = node["id"]
                break
            if "title" in node:
                name = node["title"]
            if name == node_name:
                node_id = node["id"]
                break
        if node_id is not None:
            values = prompt[str(node_id)]
            if "inputs" in values:
                if widget_name in values["inputs"]:
                    return values["inputs"][widget_name]
            raise NameError(f"Widget not found: {node_name}.{widget_name}")
        raise NameError(f"Node not found: {node_name}.{widget_name}")

    def evaluate(self, expression, extra_pnginfo, prompt, a=None, b=None, c=None):
        expression = expression.replace('\n', ' ').replace('\r', '')
        node = ast.parse(expression, mode='eval').body

        def eval_expr(node):
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.BinOp):
                return operators[type(node.op)](eval_expr(node.left), eval_expr(node.right))
            elif isinstance(node, ast.UnaryOp):
                return operators[type(node.op)](eval_expr(node.operand))
            elif isinstance(node, ast.Attribute):
                return self.get_widget_value(extra_pnginfo, prompt, node.value.id, node.attr)
            elif isinstance(node, ast.Name):
                if node.id == "a":
                    return a
                if node.id == "b":
                    return b
                if node.id == "c":
                    return c
                raise NameError(f"Name not found: {node.id}")
            elif isinstance(node, ast.Call):
                if node.func.id in functions:
                    fn = functions[node.func.id]
                    l = len(node.args)
                    if l < fn["args"][0] or l > fn["args"][1]:
                        raise SyntaxError(
                            f"Invalid function call: {node.func.id} requires {fn['args'][0]} to {fn['args'][1]} arguments")
                    args = []
                    for arg in node.args:
                        args.append(eval_expr(arg))
                    return fn["call"](*args)
                raise NameError(f"Invalid function call: {node.func.id}")
            else:
                raise TypeError(node)

        r = eval_expr(node)
        return (int(r), float(r), str(r))


NODE_CLASS_MAPPINGS = {
    "MathExpression|pysssss": MathExpression,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MathExpression|pysssss": "Math Expression 🐍",
}
