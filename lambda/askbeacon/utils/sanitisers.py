import ast


def sanitise(code: str) -> str:
    """
    Parse the given Python code string, remove all import statements,
    and return the modified code as a string.

    :param code: The Python code as a string.
    :return: The modified Python code with import statements removed.
    """

    class ImportRemover(ast.NodeTransformer):
        def visit_Import(self, node):
            # Return None to remove the node
            return None

        def visit_ImportFrom(self, node):
            # Return None to remove the node
            return None

        def visit_Expr(self, node):
            # Remove exec statements
            # Check if the expression node is an exec call
            if (
                isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and (node.value.func.id in ["exec", "eval"])
            ):
                return None
            return self.generic_visit(node)

        def visit_Call(self, node):
            # Remove 'open(...)' calls if they are direct statements
            if isinstance(node.func, ast.Name) and node.func.id == "open":
                return None
            return self.generic_visit(node)

        def visit_With(self, node):
            # Remove 'with open(...) as ...:' blocks
            if any(
                isinstance(item.context_expr, ast.Call)
                and isinstance(item.context_expr.func, ast.Name)
                and item.context_expr.func.id == "open"
                for item in node.items
            ):
                return None
            return self.generic_visit(node)

    # Parse the code into an AST
    parsed_ast = ast.parse(code)
    # Remove import statements
    remover = ImportRemover()
    modified_ast = remover.visit(parsed_ast)
    # Generate code from the modified AST
    modified_code = ast.unparse(modified_ast)
    return modified_code


if __name__ == "__main__":
    from textwrap import dedent

    # Example usage
    example_code = dedent(
        """
    import os
    import sys
    from math import sqrt

    print(open("/root/private.txt"))

    with open("/root/private.txt") as f:
        print(f.read())

    def example_function():
        import os
        exec("import os; print(os.environ)")
        eval("import sys; sys.exit(-1)")
        print("this is okay")
        return sqrt(4)
    """
    )

    print(sanitise(example_code))
