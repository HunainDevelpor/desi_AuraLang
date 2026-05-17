import os
import datetime
from typing import List, Dict, Any

class CompilerReportGenerator:
    @staticmethod
    def generate_html(data: Dict[str, Any]) -> str:
        """
        Generates a premium, beautifully styled responsive educational HTML report
        detailing the entire compilation pipeline and intermediate representations.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 1. Format Source Code
        source_code = data.get("source_code", "").strip()
        source_escaped = source_code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        # 2. Format Lexical Tokens Table
        tokens_rows = ""
        for i, t in enumerate(data.get("tokens", [])):
            tokens_rows += f"<tr><td>{i+1}</td><td><code>{t.type.name}</code></td><td><code>\"{t.value}\"</code></td><td>Line {t.line}, Col {t.col}</td></tr>\n"
            
        # 3. Format Symbols Table
        symbol_rows = ""
        for s in data.get("symbols", []):
            symbol_rows += f"<tr><td><code>{s.name}</code></td><td><span class='badge badge-blue'>{s.datatype}</span></td><td><code>{s.scope}</code></td><td><code>{s.value if s.value is not None else '-'}</code></td><td><code>{s.address}</code></td><td>Line {s.line}</td></tr>"

        # 4. Format FIRST / FOLLOW sets
        ff_rows = ""
        first = data.get("first", {})
        follow = data.get("follow", {})
        for nt in sorted(first.keys()):
            first_set = ", ".join(sorted(first[nt]))
            follow_set = ", ".join(sorted(follow.get(nt, set())))
            ff_rows += f"<tr><td><strong>{nt}</strong></td><td><code>{{ {first_set} }}</code></td><td><code>{{ {follow_set} }}</code></td></tr>"

        # 5. Format TAC instructions
        tac_code = "\n".join(data.get("tac_lines", []))
        
        # 6. Format Assembly instruction stream
        asm_code = "\n".join(data.get("asm_lines", []))
        
        # 7. Format VM console outputs
        vm_outputs = ""
        for out in data.get("vm_console", []):
            vm_outputs += f"<div class='console-line'>&gt; {out}</div>"
            
        vm_logs = "\n".join(data.get("vm_logs", []))

        html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Desi AuraLang Compiler Report</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
        
        :root {{
            --bg-color: #0c0c0d;
            --card-bg: #141416;
            --border-color: #232326;
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --accent-blue: #3b82f6;
            --accent-green: #10b981;
            --accent-orange: #f59e0b;
            --accent-red: #ef4444;
        }}

        body {{
            background-color: var(--bg-color);
            color: var(--text-primary);
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 0;
            line-height: 1.6;
        }}

        header {{
            background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
            border-bottom: 1px solid var(--border-color);
            padding: 40px 10%;
            text-align: center;
        }}

        header h1 {{
            margin: 0;
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: -0.05em;
            background: linear-gradient(to right, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        header p {{
            color: var(--text-secondary);
            margin: 10px 0 0 0;
            font-size: 1.1rem;
        }}

        .container {{
            max-width: 1200px;
            margin: 40px auto;
            padding: 0 20px;
        }}

        .card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        }}

        .card h2 {{
            margin-top: 0;
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 10px;
            font-size: 1.5rem;
            color: var(--accent-blue);
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        pre {{
            background-color: #080809;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 20px;
            overflow-x: auto;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            color: #e2e8f0;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}

        th, td {{
            text-align: left;
            padding: 12px 15px;
            border-bottom: 1px solid var(--border-color);
        }}

        th {{
            background-color: #080809;
            font-weight: 600;
            color: var(--text-secondary);
        }}

        tr:hover {{
            background-color: #19191c;
        }}

        code {{
            font-family: 'JetBrains Mono', monospace;
            background-color: #080809;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.85rem;
        }}

        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }}

        .badge-blue {{
            background-color: rgba(59, 130, 246, 0.15);
            color: #60a5fa;
        }}

        .badge-green {{
            background-color: rgba(16, 185, 129, 0.15);
            color: #34d399;
        }}

        .console {{
            background-color: #050506;
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 15px;
            font-family: 'JetBrains Mono', monospace;
            color: var(--accent-green);
        }}

        .console-line {{
            margin-bottom: 5px;
        }}

        footer {{
            text-align: center;
            padding: 40px 0;
            color: var(--text-secondary);
            border-top: 1px solid var(--border-color);
            margin-top: 60px;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>

    <header>
        <h1>Desi AuraLang Compilation Dossier</h1>
        <p>Complete Pipeline Diagnostic Report &amp; Visual Compiler Symbols</p>
        <div style="margin-top:15px; font-size:0.85rem; color:var(--text-secondary);">
            Generated on: <strong>{timestamp}</strong>
        </div>
    </header>

    <div class="container">
        
        <!-- 1. SOURCE CODE -->
        <div class="card">
            <h2>📝 SOURCE CODE INPUT</h2>
            <pre><code>{source_escaped}</code></pre>
        </div>

        <!-- 2. LEXICAL TOKENS -->
        <div class="card">
            <h2>🔍 PHASE 1: LEXICAL TOKENS LIST</h2>
            <table>
                <thead>
                    <tr>
                        <th style="width: 80px;">Index</th>
                        <th>Token Type</th>
                        <th>Lexeme / Value</th>
                        <th>Location Coordinates</th>
                    </tr>
                </thead>
                <tbody>
                    {tokens_rows}
                </tbody>
            </table>
        </div>

        <!-- 3. LL(1) GRAMMAR ANALYSIS -->
        <div class="card">
            <h2>📊 PHASE 2: LL(1) GRAMMARSETS</h2>
            <table>
                <thead>
                    <tr>
                        <th>Non-Terminal</th>
                        <th>FIRST Set</th>
                        <th>FOLLOW Set</th>
                    </tr>
                </thead>
                <tbody>
                    {ff_rows}
                </tbody>
            </table>
        </div>

        <!-- 4. SEMANTIC CHECKER SYMBOLS -->
        <div class="card">
            <h2>🔑 PHASE 3 &amp; 4: SCOPED SYMBOLS REGISTRY</h2>
            <table>
                <thead>
                    <tr>
                        <th>Identifier</th>
                        <th>Type Bind</th>
                        <th>Scope Depth</th>
                        <th>Assigned Value</th>
                        <th>Memory Offset</th>
                        <th>Source Location</th>
                    </tr>
                </thead>
                <tbody>
                    {symbol_rows}
                </tbody>
            </table>
        </div>

        <!-- 5. THREE ADDRESS CODE -->
        <div class="card">
            <h2>⚙️ PHASE 5: INTERMEDIATE CODE (TAC)</h2>
            <pre><code>{tac_code}</code></pre>
        </div>

        <!-- 6. TARGET VM ASSEMBLY -->
        <div class="card">
            <h2>💾 PHASE 6: STACK VM ASSEMBLY CODE</h2>
            <pre><code>{asm_code}</code></pre>
        </div>

        <!-- 7. VM CPU EXECUTION TRACE -->
        <div class="card">
            <h2>🖥️ virtual machine runtime console</h2>
            <div class="console">
                {vm_outputs if vm_outputs else "<div class='console-line'>Console output empty. Run step debugging simulation first.</div>"}
            </div>
            <h3 style="margin-top:20px; font-size:1.1rem; color:var(--text-secondary);">VM Execution Logs</h3>
            <pre><code>{vm_logs if vm_logs else "No simulation steps recorded."}</code></pre>
        </div>

    </div>

    <footer>
        <p>&copy; Desi AuraLang Educational Visual Compiler. Statically compiled to Stack VM Bytecode.</p>
    </footer>

</body>
</html>
"""
        return html_template

    @staticmethod
    def generate_txt(data: Dict[str, Any]) -> str:
        """Generates a plain-text dossier report representing the compiler stats."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        source_code = data.get("source_code", "").strip()
        
        tokens_str = ""
        for i, t in enumerate(data.get("tokens", [])):
            tokens_str += f"[{i+1:3}] {t.type.name:<15} | \"{t.value}\":<{15} | Line {t.line}, Col {t.col}\n"
            
        syms_str = ""
        for s in data.get("symbols", []):
            syms_str += f"- {s.name:<12} | Type: {s.datatype:<10} | Scope: {s.scope:<12} | Addr: {s.address:<6} | Line {s.line}\n"
            
        tac_code = "\n".join(data.get("tac_lines", []))
        asm_code = "\n".join(data.get("asm_lines", []))
        
        vm_outs = "\n".join([f"> {out}" for out in data.get("vm_console", [])])
        vm_logs = "\n".join(data.get("vm_logs", []))

        text_report = f"""====================================================
DESI AURALANG COMPILER ANALYSIS DOSSIER
====================================================
Generated on: {timestamp}

[1. ORIGINAL SOURCE CODE]
----------------------------------------------------
{source_code}

[2. LEXICAL TOKENS (PHASE 1)]
----------------------------------------------------
{tokens_str}

[3. SCOPED SYMBOL TABLE (PHASE 4)]
----------------------------------------------------
{syms_str}

[4. THREE ADDRESS INTERMEDIATE CODE (PHASE 5)]
----------------------------------------------------
{tac_code}

[5. TARGET ASSEMBLY STREAM (PHASE 6)]
----------------------------------------------------
{asm_code}

[6. VM RUNTIME OUTPUT CONSOLE]
----------------------------------------------------
{vm_outs if vm_outs else "No output printed."}

VM LOG TRACE:
{vm_logs if vm_logs else "No vm execution trace."}
====================================================
"""
        return text_report
