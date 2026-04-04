from __future__ import annotations

import os
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont
from tkinter import messagebox, ttk

from .session import SessionRuntime


class RuntimeGui:
    def __init__(self, session_id: str, base_dir: str | Path = "data/runtime") -> None:
        self.runtime = SessionRuntime(session_id=session_id, base_dir=base_dir)
        os.environ.setdefault("LANG", "C.UTF-8")
        os.environ.setdefault("LC_CTYPE", os.environ.get("LANG", "C.UTF-8"))
        os.environ.setdefault("XMODIFIERS", "@im=ibus")
        self.root = tk.Tk()
        self.root.title(f"PBL User Runtime - {session_id}")
        self.root.geometry("900x720")
        self.root.minsize(820, 640)
        self.root.tk.call("tk", "useinputmethods", True)
        self._configure_fonts()
        self.phase_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="")
        self.hand_var = tk.StringVar(value="")
        self.end_var = tk.StringVar(value="")
        self.topic_var = tk.StringVar(value="")
        self.selected_var = tk.StringVar(value="尚未被选中发言")
        self.prompt_var = tk.StringVar(value="")
        self.chat_hint_var = tk.StringVar(value="学生发言请通过对话界面使用 /pbl-say 提交。")
        self._build()
        if not self.has_cjk_font:
            self.root.after(100, self._show_missing_font_warning)
        self.refresh()
        self.root.after(1000, self._auto_refresh)

    def _configure_fonts(self) -> None:
        families = set(tkfont.families(self.root))
        family, has_cjk_font = self._pick_font_family(families)
        self.has_cjk_font = has_cjk_font

        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family=family, size=11)

        text_font = tkfont.nametofont("TkTextFont")
        text_font.configure(family=family, size=11)

        heading_font = tkfont.nametofont("TkHeadingFont")
        heading_font.configure(family=family, size=12, weight="bold")

        style = ttk.Style(self.root)
        style.configure(".", font=default_font)

        self.header_font = heading_font.copy()
        self.header_font.configure(size=16, weight="bold")
        self.emphasis_font = heading_font.copy()

    @staticmethod
    def _pick_font_family(families: set[str]) -> tuple[str, bool]:
        preferred = os.environ.get("PBL_GUI_FONT_FAMILY", "").strip()
        if preferred and preferred in families:
            return preferred, True

        candidates = [
            "Noto Sans CJK SC",
            "Noto Sans SC",
            "Source Han Sans SC",
            "Source Han Sans CN",
            "Sarasa UI SC",
            "WenQuanYi Micro Hei",
            "Microsoft YaHei UI",
            "Microsoft YaHei",
            "PingFang SC",
            "Hiragino Sans GB",
            "SimHei",
            "SimSun",
            "Arial Unicode MS",
            "DejaVu Sans",
        ]
        for candidate in candidates:
            if candidate in families:
                return candidate, candidate != "DejaVu Sans"
        return tkfont.nametofont("TkDefaultFont").cget("family"), False

    def _show_missing_font_warning(self) -> None:
        messagebox.showwarning(
            "Missing Chinese Font",
            "The current environment does not have a Chinese-capable font installed. "
            "Please install a CJK font such as Noto Sans CJK SC or WenQuanYi Micro Hei, "
            "or start the GUI with PBL_GUI_FONT_FAMILY set to an installed Chinese font.",
        )

    def _build(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(3, weight=1)

        header = ttk.Label(frame, text="PBL 用户参与运行时", font=self.header_font)
        header.grid(row=0, column=0, sticky="w")

        meta = ttk.Frame(frame)
        meta.grid(row=1, column=0, sticky="ew", pady=(12, 10))
        meta.columnconfigure(1, weight=1)
        for label, var in [
            ("讨论主题", self.topic_var),
            ("当前阶段", self.phase_var),
            ("运行状态", self.status_var),
            ("学生举手", self.hand_var),
            ("结束意愿", self.end_var),
        ]:
            row_index = len(meta.grid_slaves(column=0))
            ttk.Label(meta, text=f"{label}:", width=10).grid(row=row_index, column=0, sticky="nw", pady=1)
            ttk.Label(meta, textvariable=var, wraplength=720, justify=tk.LEFT).grid(row=row_index, column=1, sticky="w", pady=1)

        selected_box = ttk.LabelFrame(frame, text="发言提示", padding=12)
        selected_box.grid(row=2, column=0, sticky="ew", pady=(8, 12))
        selected_box.columnconfigure(0, weight=1)
        ttk.Label(selected_box, textvariable=self.selected_var, font=self.emphasis_font).grid(row=0, column=0, sticky="w")
        ttk.Label(selected_box, textvariable=self.prompt_var, wraplength=760, justify=tk.LEFT).grid(row=1, column=0, sticky="w", pady=(6, 0))

        editor_box = ttk.LabelFrame(frame, text="学生操作区", padding=12)
        editor_box.grid(row=3, column=0, sticky="nsew")
        editor_box.columnconfigure(0, weight=1)
        editor_box.rowconfigure(1, weight=1)

        controls = ttk.Frame(editor_box)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(controls, text="举手", command=self.raise_hand).pack(side=tk.LEFT)
        ttk.Button(controls, text="放下手", command=self.lower_hand).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(controls, text="想结束研讨", command=self.request_end_discussion).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(controls, text="继续讨论", command=self.clear_end_discussion).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(controls, text="刷新", command=self.refresh).pack(side=tk.LEFT, padx=(8, 0))

        chat_box = ttk.Frame(editor_box)
        chat_box.grid(row=1, column=0, sticky="nsew")
        chat_box.columnconfigure(0, weight=1)
        ttk.Label(
            chat_box,
            textvariable=self.chat_hint_var,
            wraplength=760,
            justify=tk.LEFT,
        ).grid(row=0, column=0, sticky="nw")

    def _enqueue(self, payload: dict[str, str]) -> None:
        self.runtime.enqueue_event(payload)
        self.runtime.process_inbox_once()
        self.refresh()

    def raise_hand(self) -> None:
        self._enqueue({"type": "HAND_RAISED", "source": "gui"})

    def lower_hand(self) -> None:
        self._enqueue({"type": "HAND_LOWERED", "source": "gui"})

    def request_end_discussion(self) -> None:
        self._enqueue({"type": "END_DISCUSSION_REQUESTED", "source": "gui"})

    def clear_end_discussion(self) -> None:
        self._enqueue({"type": "END_DISCUSSION_CLEARED", "source": "gui"})

    def refresh(self) -> None:
        state = self.runtime.read_state()
        student = state["participants"]["student"]
        runtime = state["runtime"]
        effective_state = student.get("effective_state_card") or {}
        self.topic_var.set(state.get("topic", ""))
        self.phase_var.set(state.get("phase", ""))
        self.status_var.set(state.get("status", ""))
        self.hand_var.set(str(student.get("effective_hand_raised", False)))
        self.end_var.set(str(effective_state.get("can_end_discussion", False)))
        if runtime.get("student_selected_to_speak"):
            self.selected_var.set("已选中你发言，请输入并提交。")
            self.chat_hint_var.set("请回到 OpenCode 对话界面，使用 /pbl-say 加上你的发言内容提交。")
        else:
            self.selected_var.set("尚未被选中发言")
            self.chat_hint_var.set("你可以在这里举手；真正发言请在被选中后回到对话界面使用 /pbl-say。")
        self.prompt_var.set(runtime.get("selection_prompt", ""))

    def _auto_refresh(self) -> None:
        try:
            self.refresh()
        finally:
            self.root.after(1000, self._auto_refresh)

    def run(self) -> None:
        self.root.mainloop()


def launch_gui(session_id: str, base_dir: str | Path = "data/runtime") -> None:
    RuntimeGui(session_id=session_id, base_dir=base_dir).run()


if __name__ == "__main__":
    runtime = SessionRuntime.from_current()
    launch_gui(runtime.session_id, runtime.base_dir)
