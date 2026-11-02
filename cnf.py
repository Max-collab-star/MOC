class CFGConverter:

    def __init__(self, raw_rules, start_symbol="S"):
        self.start_symbol = start_symbol
        self.rules = self._parse_rules(raw_rules)
        self.steps = {}

    def _parse_rules(self, raw_rules):
        rules = {}
        for line in raw_rules.strip().split("\n"):
            if "->" not in line:
                continue
            lhs, rhs = line.split("->")
            lhs = lhs.strip()
            productions = [p.strip() for p in rhs.split("|")]
            if lhs not in rules:
                rules[lhs] = set()
            for p in productions:
                # Normalize epsilon representations (eps, EPS, ε) to ""
                if p in ["ε", "eps", "EPS", "e", "E"]:
                    p = ""
                rules[lhs].add(p)
        return rules

    def get_rules_string(self, rule_dict):
        lines = []
        for lhs in sorted(rule_dict.keys()):
            prods = sorted(list(rule_dict[lhs]))
            # Format empty string as ε for clean display
            prods_formatted = ["ε" if p == "" else p for p in prods]
            lines.append(f"{lhs} -> {' | '.join(prods_formatted)}")
        return "\n".join(lines)

    def to_cnf(self):
        r = {k: set(v) for k, v in self.rules.items()}
        self.steps["1. Initial Rules"] = self.get_rules_string(r)

        # Step 1: Add new start symbol to prevent start symbol on RHS
        new_start = self.start_symbol + "'"
        while new_start in r:
            new_start += "'"
        r[new_start] = {self.start_symbol}
        original_start = self.start_symbol
        self.start_symbol = new_start

        # Step 2: Eliminate Epsilon productions correctly
        r = self._eliminate_epsilons(r, original_start)
        self.steps["2. After ε-Elimination"] = self.get_rules_string(r)

        # Step 3: Eliminate Unit productions
        r = self._eliminate_units(r)
        self.steps["3. After Unit Production Elimination"] = (
            self.get_rules_string(r)
        )

        # Step 4: Eliminate Useless symbols
        r = self._eliminate_useless(r)
        self.steps["4. After Useless Symbol Elimination"] = (
            self.get_rules_string(r)
        )

        # Step 5: Convert to Binary CNF form
        r = self._convert_to_binary(r)
        self.steps["5. Final Chomsky Normal Form (CNF)"] = (
            self.get_rules_string(r)
        )

        return r

    def _eliminate_epsilons(self, r, original_start):
        # Find all nullable variables
        nullable = set()
        changed = True
        while changed:
            changed = False
            for lhs, prods in r.items():
                if lhs in nullable:
                    continue
                for prod in prods:
                    if prod == "" or all(sym in nullable for sym in prod):
                        nullable.add(lhs)
                        changed = True
                        break

        # Generate new productions by omitting nullable symbols
        new_r = {}
        for lhs, prods in r.items():
            new_r[lhs] = set()
            for prod in prods:
                if prod == "":
                    continue  # Drop epsilon rules entirely from non-start processing

                # Generate all index combinations for nullable characters in prod
                # e.g., if prod is AB and A is nullable, combinations are AB and B
                import itertools

                indices = [i for i, sym in enumerate(prod) if sym in nullable]

                for k in range(len(indices) + 1):
                    for combo in itertools.combinations(indices, k):
                        # combo contains indices to remove
                        new_prod = "".join(
                            [
                                sym
                                for i, sym in enumerate(prod)
                                if i not in combo
                            ]
                        )
                        if new_prod != "":
                            new_r[lhs].add(new_prod)

        # Clean up empty sets
        new_r = {k: v for k, v in new_r.items() if v}

        # If original start symbol was nullable, allow S0 -> ε or handle at top level
        if original_start in nullable and self.start_symbol in new_r:
            new_r[self.start_symbol].add("")

        return new_r

    def _eliminate_units(self, r):
        unit_pairs = {lhs: {lhs} for lhs in r}
        changed = True
        while changed:
            changed = False
            for A in r:
                for prod in list(r[A]):
                    if len(prod) == 1 and prod in r:
                        B = prod
                        for b in unit_pairs[B]:
                            if b not in unit_pairs[A]:
                                unit_pairs[A].add(b)
                                changed = True

        new_r = {lhs: set() for lhs in r}
        for A in r:
            for B in unit_pairs[A]:
                if B in r:
                    for prod in r[B]:
                        if not (len(prod) == 1 and prod in r):
                            new_r[A].add(prod)
        return {k: v for k, v in new_r.items() if v}

    def _eliminate_useless(self, r):
        generating = set()
        changed = True
        while changed:
            changed = False
            for lhs, prods in r.items():
                if lhs in generating:
                    continue
                for prod in prods:
                    if all(
                        sym.islower() or sym in generating or sym == ""
                        for sym in prod
                    ):
                        generating.add(lhs)
                        changed = True
                        break

        r = {
            lhs: {
                prod
                for prod in prods
                if all(
                    s.islower() or s in generating for s in prod if s != ""
                )
            }
            for lhs, prods in r.items()
            if lhs in generating
        }

        reachable = {self.start_symbol}
        queue = [self.start_symbol]
        while queue:
            curr = queue.pop(0)
            if curr in r:
                for prod in r[curr]:
                    for sym in prod:
                        if sym.isupper() and sym not in reachable:
                            reachable.add(sym)
                            queue.append(sym)

        return {lhs: prods for lhs, prods in r.items() if lhs in reachable}

    def _convert_to_binary(self, r):
        new_r = {}
        term_map = {}  # maps terminals to variables (e.g., 'a' -> 'X1')
        binary_map = {}  # maps binary pairs to variables (e.g., 'SA' -> 'Y1')
        var_count = 1

        for lhs, prods in r.items():
            new_r[lhs] = set()
            for prod in prods:
                if prod == "":
                    new_r[lhs].add("")
                    continue
                if len(prod) <= 2 and all(s.isupper() for s in prod):
                    new_r[lhs].add(prod)
                    continue
                if len(prod) == 1 and not prod.isupper():
                    new_r[lhs].add(prod)
                    continue

                current_prod = []
                for sym in prod:
                    if not sym.isupper():
                        if sym not in term_map:
                            new_var = f"X{var_count}"
                            var_count += 1
                            term_map[sym] = new_var
                            new_r[new_var] = {sym}
                        current_prod.append(term_map[sym])
                    else:
                        current_prod.append(sym)

                # Break down long productions into binary chains and REUSE variables for duplicate pairs
                while len(current_prod) > 2:
                    pair = "".join(current_prod[-2:])
                    if pair not in binary_map:
                        new_var = f"Y{var_count}"
                        var_count += 1
                        binary_map[pair] = new_var
                        if new_var not in new_r:
                            new_r[new_var] = set()
                        new_r[new_var].add(pair)
                    
                    current_prod = current_prod[:-2] + [binary_map[pair]]

                combined = "".join(current_prod)
                new_r[lhs].add(combined)
        return new_r