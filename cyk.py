import re

class CYKParser:

    def __init__(self, grammar, start_symbol="S"):
        self.grammar = grammar
        self.start_symbol = start_symbol

    def _tokenize(self, prod):
        if not prod:
            return []
        # Extract variables (uppercase letters followed by optional primes/digits) or terminals
        return re.findall(r"[A-Z]['0-9]*|[a-z]", prod)

    def parse(self, string):
        n = len(string)
        if n == 0:
            return False, []

        table = [[set() for _ in range(n - i)] for i in range(n)]

        # Step 1: Fill base rules for substrings of length 1
        for j in range(n):
            char = string[j]
            for lhs, productions in self.grammar.items():
                for prod in productions:
                    symbols = self._tokenize(prod)
                    if len(symbols) == 1 and symbols[0] == char:
                        table[0][j].add(lhs)

        # Step 2: Fill for lengths 2 to n
        for length in range(2, n + 1):  # length of substring
            for j in range(n - length + 1):  # start index
                for k in range(1, length):  # partition point
                    left_set = table[k - 1][j]
                    right_set = table[length - k - 1][j + k]

                    for lhs, productions in self.grammar.items():
                        for prod in productions:
                            symbols = self._tokenize(prod)
                            if len(symbols) == 2:
                                b, c = symbols[0], symbols[1]
                                if b in left_set and c in right_set:
                                    table[length - 1][j].add(lhs)

        top_cell = table[n - 1][0] if n > 0 else set()
        accepted = (
            self.start_symbol in top_cell
            or "S" in top_cell
            or any(s.startswith("S'") or s == "S" for s in top_cell)
        )

        return accepted, table