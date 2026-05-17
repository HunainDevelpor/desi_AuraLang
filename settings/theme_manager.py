import customtkinter as ctk
import tkinter as tk

class ThemeManager:
    def __init__(self, app):
        self.app = app
        
        # Color Palettes
        self.themes = {
            "Dark": {
                "bg_color": "#0c0c0d",
                "card_bg": "#141416",
                "sidebar_bg": "#0a0a0a",
                "editor_bg": "#0f0f10",
                "editor_fg": "#f1f1f1",
                "text_primary": "#ffffff",
                "text_secondary": "#9ca3af",
                "accent_blue": "#3b82f6",
                "accent_green": "#10b981",
                "border_color": "#232326"
            },
            "Light": {
                "bg_color": "#f3f4f6",
                "card_bg": "#ffffff",
                "sidebar_bg": "#f9fafb",
                "editor_bg": "#ffffff",
                "editor_fg": "#1f2937",
                "text_primary": "#111827",
                "text_secondary": "#4b5563",
                "accent_blue": "#2563eb",
                "accent_green": "#059669",
                "border_color": "#e5e7eb"
            }
        }

    def apply_theme(self, theme_name: str):
        if theme_name not in self.themes:
            return
            
        colors = self.themes[theme_name]
        ctk.set_appearance_mode(theme_name)
        
        # 1. Update main window backgrounds
        self.app.configure(fg_color=colors["bg_color"])
        self.app.sidebar_canvas_frame.configure(fg_color=colors["sidebar_bg"])
        self.app.main_content.configure(fg_color=colors["card_bg"])
        self.app.console_panel.configure(fg_color=colors["card_bg"])
        
        # 2. Update specific visual components
        # Code Editor
        if hasattr(self.app, "code_editor"):
            self.app.code_editor.configure(fg_color=colors["card_bg"])
            self.app.code_editor.editor.configure(
                bg=colors["editor_bg"],
                fg=colors["editor_fg"],
                insertbackground=colors["text_primary"]
            )
            
        # Textboxes
        textboxes = [
            "orig_tac_text", "opt_tac_text", "opt_log_text",
            "asm_textbox", "vm_console_text", "log_terminal",
            "err_terminal", "tac_textbox"
        ]
        for name in textboxes:
            if hasattr(self.app, name):
                tb = getattr(self.app, name)
                tb.configure(
                    fg_color=colors["editor_bg"],
                    text_color=colors["editor_fg"]
                )
                
        # Custom Canvas backdrops (e.g. flowchart & pipeline viz)
        if hasattr(self.app, "pipeline_viz"):
            self.app.pipeline_viz.configure(fg_color="transparent")
            self.app.pipeline_viz.canvas.configure(bg=colors["editor_bg"])
            self.app.pipeline_viz.controls.configure(fg_color=colors["card_bg"])
            
        # Tree & AST Canvases
        if hasattr(self.app, "tree_viz"):
            self.app.tree_viz.configure(bg=colors["editor_bg"])
        if hasattr(self.app, "ast_viz"):
            self.app.ast_viz.configure(bg=colors["editor_bg"])
        if hasattr(self.app, "cfg_flow_viz"):
            self.app.cfg_flow_viz.configure(bg=colors["editor_bg"])

        # Telemetry Analytics Dashboard
        if hasattr(self.app, "tabs") and "analytics" in self.app.tabs:
            analytics = self.app.tabs["analytics"]
            analytics.configure(fg_color="transparent")
            analytics.gauges_frame.configure(fg_color=colors["card_bg"])
            analytics.chart_frame.configure(fg_color=colors["card_bg"])
            analytics.bar_canvas.configure(bg=colors["editor_bg"])
            analytics.line_canvas.configure(bg=colors["editor_bg"])
            
        # Re-apply active highlights with matching palette contrast
        if hasattr(self.app, "update_debugger_highlights"):
            self.app.update_debugger_highlights()
            
        self.app.log_compiler(f"Dynamic layout styling overrode to {theme_name.upper()} theme successfully.")
