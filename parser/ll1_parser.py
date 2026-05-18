from .grammer import TERMINALS

class Node:
    def __init__(self, value):
        self.value = value
        self.children = []
    
    def add_child(self, node):
        self.children.append(node)
    
    def to_dict(self):
        return {
            "name": self.value,
            "children": [c.to_dict() for c in self.children]
        }

class LL1Parser:
    def __init__(self, table, grammar):
        self.table = table
        self.grammar = grammar
        self.start_symbol = list(grammar.keys())[0]

    def parse(self, tokens_objs):
        # Convert lexer tokens to grammar terminals
        input_tokens = []
        for t in tokens_objs:
            # Map token type to grammar terminal string. If not in TERMINALS, fallback to name or value
            g_terminal = TERMINALS.get(t.type.name)
            if g_terminal is None:
                g_terminal = str(t.value) if t.value is not None else t.type.name.lower()
            
            literal = str(t.value) if t.value is not None else g_terminal
            input_tokens.append((g_terminal, literal)) # (terminal, literal)
        
        # Add EOF
        if not input_tokens or input_tokens[-1][0] != "$":
            input_tokens.append(("$", "$"))

        stack = ["$", self.start_symbol]
        
        # Root of parse tree
        root = Node(self.start_symbol)
        node_stack = ["$", root]
        
        trace = []
        error = None
        
        while stack:
            top = stack[-1]
            current_token_term, current_token_val = input_tokens[0]
            
            stack_view = " ".join(stack)
            input_view = " ".join([t[0] for t in input_tokens])
            
            if top == current_token_term:
                # Match
                stack.pop()
                node = node_stack.pop()
                # If it's a leaf node that is a terminal, we might want to store the literal value
                if node != "$":
                    node.value = f"{node.value} ({current_token_val})" if current_token_val != current_token_term else node.value
                
                input_tokens.pop(0)
                trace.append({
                    "stack": stack_view,
                    "input": input_view,
                    "action": f"Match {current_token_term}"
                })
            elif top in self.grammar:
                # Non-terminal
                if current_token_term in self.table[top]:
                    prod = self.table[top][current_token_term]
                    stack.pop()
                    parent_node = node_stack.pop()
                    
                    trace.append({
                        "stack": stack_view,
                        "input": input_view,
                        "action": f"Expand {top} -> {' '.join(prod)}"
                    })
                    
                    if prod != ["\u03b5"]:
                        # Push in reverse order
                        for symbol in reversed(prod):
                            stack.append(symbol)
                            child_node = Node(symbol)
                            parent_node.children.insert(0, child_node)
                            node_stack.append(child_node)
                    else:
                        # Epsilon production
                        parent_node.add_child(Node("\u03b5"))
                else:
                    error = f"Syntax Error: No rule for {top} with input {current_token_term}"
                    break
            elif top == "$":
                if current_token_term == "$":
                    trace.append({
                        "stack": stack_view,
                        "input": input_view,
                        "action": "Accept"
                    })
                    stack.pop()
                else:
                    error = f"Syntax Error: Unexpected input {current_token_term}"
                    break
            else:
                error = f"Syntax Error: Expected {top} but found {current_token_term}"
                break
                
        return {
            "success": error is None,
            "error": error,
            "trace": trace,
            "tree": root.to_dict() if error is None else None
        }