import ast


def remove_imports(code: str) -> str:
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

    def example_function():
        import os
        return sqrt(4)
    """
    )

    print(remove_imports(example_code))
