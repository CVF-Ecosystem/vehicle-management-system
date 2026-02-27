# ui/components.py
import customtkinter as ctk
from tkinter import Menu, Toplevel, Label, messagebox, ttk, Listbox, END
from tkcalendar import DateEntry
from datetime import datetime
from data_normalizer import normalizer
from translations import translations


def harmonize_combobox_style(combo: ctk.CTkComboBox) -> None:
    """Apply a minimal, stable theme pass to CTkComboBox.

    Note: forcing CTkComboBox to mimic CTkEntry (fg/border/corner) can render
    poorly on some systems (e.g., border appears only at the rounded ends).
    This helper keeps CTkComboBox's native styling and only applies best-effort
    dropdown/button/menu colors from theme tokens.
    """
    try:
        button_theme = ctk.ThemeManager.theme.get("CTkButton", {})
        dropdown_theme = ctk.ThemeManager.theme.get("DropdownMenu", {})

        desired_config = {
            # Keep dropdown button theme-consistent.
            "button_color": button_theme.get("fg_color"),
            "button_hover_color": button_theme.get("hover_color"),

            # Dropdown menu colors (if supported by the installed CTk version).
            "dropdown_fg_color": dropdown_theme.get("fg_color"),
            "dropdown_hover_color": dropdown_theme.get("hover_color"),
            "dropdown_text_color": dropdown_theme.get("text_color"),
        }

        # Apply best-effort, skipping None and unsupported keys.
        for key, value in desired_config.items():
            if value is None:
                continue
            try:
                combo.configure(**{key: value})
            except Exception:
                continue
    except Exception:
        # Best-effort styling only; never break UI construction.
        return


# === PHASE 2.5: AutocompleteEntry Widget ===
class AutocompleteEntry(ctk.CTkFrame):
    """
    Entry widget với tính năng gợi ý tự động (autocomplete).
    Hiển thị dropdown listbox với các gợi ý khi người dùng nhập.
    Có thể thêm nút dropdown để xổ toàn bộ danh sách.
    """
    def __init__(self, parent, suggestions=None, max_suggestions=10, show_dropdown_button=True, **kwargs):
        """
        Args:
            parent: Parent widget
            suggestions: List hoặc function trả về list gợi ý
            max_suggestions: Số lượng gợi ý tối đa hiển thị
            show_dropdown_button: Hiển thị nút dropdown (▼) bên phải
            **kwargs: Các thuộc tính khác cho CTkEntry
        """
        # Tạo frame container với border giống entry chuẩn của CTk (theo theme hiện tại)
        entry_theme = ctk.ThemeManager.theme.get("CTkEntry", {})
        entry_fg = entry_theme.get("fg_color", ("gray95", "gray17"))
        entry_border = entry_theme.get("border_color", ("gray65", "gray28"))
        entry_corner_radius = entry_theme.get("corner_radius", 6)
        entry_border_width = entry_theme.get("border_width", 2)

        super().__init__(
            parent,
            fg_color=entry_fg,
            corner_radius=entry_corner_radius,
            border_width=entry_border_width,
            border_color=entry_border,
        )
        
        self._suggestions = suggestions if suggestions else []
        self._suggestions_func = None
        if callable(suggestions):
            self._suggestions_func = suggestions
            self._suggestions = []
        
        self._max_suggestions = max_suggestions
        self._listbox_visible = False
        self._show_dropdown_button = show_dropdown_button
        self._ignore_focus_out_once = False
        
        # Extract entry-specific kwargs (exclude border settings since we handle them)
        entry_kwargs = {k: v for k, v in kwargs.items() if k in [
            'width', 'height', 'placeholder_text_color',
            'placeholder_text', 'font', 'state', 'textvariable'
        ]}
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        # Create entry without border (border is on the frame)
        self.entry = ctk.CTkEntry(
            self, 
            border_width=0, 
            fg_color="transparent",
            **entry_kwargs
        )
        inner_pad_y = max(int(entry_border_width), 1)
        self.entry.grid(row=0, column=0, sticky="ew", padx=(6, 0), pady=inner_pad_y)
        
        # Create dropdown button if enabled - keep it subtle and theme-consistent
        if self._show_dropdown_button:
            label_theme = ctk.ThemeManager.theme.get("CTkLabel", {})
            button_theme = ctk.ThemeManager.theme.get("CTkButton", {})
            text_color = label_theme.get("text_color", ("gray10", "gray90"))

            # Match primary button (e.g. "Tìm kiếm") for a clear, consistent affordance.
            btn_color = button_theme.get("fg_color")
            btn_hover = button_theme.get("hover_color")

            # Size/shape: align with entry corner and height.
            desired_height = entry_kwargs.get("height")
            if desired_height is None:
                try:
                    desired_height = int(self.entry.cget("height"))
                except Exception:
                    desired_height = 28

            btn_corner = max(int(entry_corner_radius) - 1, 0)
            self._dropdown_btn = ctk.CTkButton(
                self, 
                text="▼", 
                width=30,
                height=desired_height - 4,
                corner_radius=btn_corner,
                command=self._toggle_dropdown,
                fg_color=btn_color,
                hover_color=btn_hover,
                text_color=text_color,
                font=("Arial", 10),
            )
            self._dropdown_btn.grid(row=0, column=1, padx=(2, 4), pady=inner_pad_y)
            self._dropdown_btn.bind("<Button-1>", self._on_dropdown_btn_press)
        
        # Create popup window for listbox
        self._popup = None
        self._listbox = None
        
        # Bind events
        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<Down>", self._on_arrow_down)
        self.entry.bind("<Up>", self._on_arrow_up)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Escape>", self._hide_listbox)
        self.entry.bind("<Tab>", self._on_tab)
        
        # Bind focus events to change border color
        self.entry.bind("<FocusIn>", self._on_focus_in)
    
    def _on_focus_in(self, event):
        """Highlight border when focused."""
        entry_theme = ctk.ThemeManager.theme.get("CTkEntry", {})
        focus_border = entry_theme.get("border_color_hover") or entry_theme.get("border_color")
        if focus_border is not None:
            self.configure(border_color=focus_border)

    def _on_dropdown_btn_press(self, event):
        """Prevent FocusOut auto-hide when opening suggestions via button."""
        self._ignore_focus_out_once = True
        self.after(0, self.entry.focus_set)
        return None
    
    def _toggle_dropdown(self):
        """Toggle hiển thị dropdown với toàn bộ danh sách."""
        # Clicking the button can trigger Entry FocusOut; suppress the auto-hide once.
        self._ignore_focus_out_once = True
        if self._listbox_visible:
            self._hide_listbox()
        else:
            self._show_all_suggestions()
    
    def _show_all_suggestions(self):
        """Hiển thị toàn bộ danh sách suggestions (khi click nút dropdown)."""
        # Refresh suggestions if using function
        if self._suggestions_func:
            self._suggestions = self._suggestions_func()
        
        if self._suggestions:
            self._show_listbox(self._suggestions, show_all=True)
            self.entry.focus_set()
        
    def _create_listbox(self):
        """Tạo popup listbox nếu chưa có."""
        if self._popup is None:
            def _pick_color(value, fallback):
                if value is None:
                    return fallback
                if isinstance(value, (list, tuple)):
                    return value[1] if ctk.get_appearance_mode() == "Dark" else value[0]
                return value

            frame_theme = ctk.ThemeManager.theme.get("CTkFrame", {})
            label_theme = ctk.ThemeManager.theme.get("CTkLabel", {})
            button_theme = ctk.ThemeManager.theme.get("CTkButton", {})

            bg = _pick_color(frame_theme.get("fg_color"), "#ffffff")
            fg = _pick_color(label_theme.get("text_color"), "#000000")
            selected_bg = _pick_color(button_theme.get("fg_color"), "#1f538d")

            self._popup = Toplevel(self)
            self._popup.withdraw()
            self._popup.overrideredirect(True)
            self._popup.attributes("-topmost", True)
            
            # Frame chứa listbox và scrollbar
            self._listbox_frame = ctk.CTkFrame(self._popup, fg_color=bg)
            self._listbox_frame.pack(fill="both", expand=True)
            
            self._listbox = Listbox(
                self._listbox_frame,
                font=("Arial", 11),
                selectmode="single",
                activestyle="dotbox",
                exportselection=False,
                bg=bg,
                fg=fg,
                selectbackground=selected_bg,
                selectforeground=fg,
                highlightthickness=0,
                borderwidth=1,
                relief="solid"
            )
            self._listbox.pack(side="left", fill="both", expand=True)
            
            # Scrollbar
            self._scrollbar = ctk.CTkScrollbar(self._listbox_frame, command=self._listbox.yview)
            self._listbox.configure(yscrollcommand=self._scrollbar.set)
            
            # Bind listbox events
            self._listbox.bind("<ButtonRelease-1>", self._on_listbox_click)
            self._listbox.bind("<Double-Button-1>", self._on_listbox_double_click)
    
    def _show_listbox(self, suggestions, show_all=False):
        """Hiển thị listbox với danh sách gợi ý."""
        if not suggestions:
            self._hide_listbox()
            return
            
        self._create_listbox()
        
        # Clear and populate listbox
        self._listbox.delete(0, END)
        
        # Khi show_all, hiển thị nhiều hơn
        max_items = 15 if show_all else self._max_suggestions
        for item in suggestions[:max_items]:
            self._listbox.insert(END, item)
        
        # Show scrollbar if needed
        if len(suggestions) > max_items:
            self._scrollbar.pack(side="right", fill="y")
        else:
            self._scrollbar.pack_forget()
        
        # Calculate position
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        # Width includes dropdown button if present
        width = self.winfo_width()
        
        # Calculate height based on items
        num_items = min(len(suggestions), max_items)
        height = num_items * 22 + 6  # ~22px per item + padding
        
        self._popup.geometry(f"{width}x{height}+{x}+{y}")
        self._popup.deiconify()
        self._listbox_visible = True
        
        # Select first item
        if num_items > 0:
            self._listbox.selection_set(0)
    
    def _hide_listbox(self, event=None):
        """Ẩn listbox."""
        if self._popup:
            self._popup.withdraw()
        self._listbox_visible = False
        return "break" if event and event.keysym == "Escape" else None
    
    def _get_filtered_suggestions(self, text):
        """Lọc danh sách gợi ý theo text nhập vào."""
        if not text:
            return []
        
        # Refresh suggestions if using function
        if self._suggestions_func:
            self._suggestions = self._suggestions_func()
        
        text_upper = text.upper()
        # Ưu tiên gợi ý bắt đầu bằng text, sau đó là chứa text
        starts_with = []
        contains = []
        
        for suggestion in self._suggestions:
            suggestion_upper = suggestion.upper()
            if suggestion_upper.startswith(text_upper):
                starts_with.append(suggestion)
            elif text_upper in suggestion_upper:
                contains.append(suggestion)
        
        return starts_with + contains
    
    def _on_key_release(self, event):
        """Xử lý khi người dùng nhập."""
        # Ignore special keys
        if event.keysym in ('Up', 'Down', 'Left', 'Right', 'Return', 'Escape', 'Tab', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R'):
            return
        
        text = self.entry.get()
        if len(text) >= 1:  # Bắt đầu gợi ý từ 1 ký tự
            suggestions = self._get_filtered_suggestions(text)
            self._show_listbox(suggestions)
        else:
            self._hide_listbox()
    
    def _on_focus_out(self, event):
        """Xử lý khi mất focus."""
        if self._ignore_focus_out_once:
            self._ignore_focus_out_once = False
            return
        # Reset border color to theme default
        entry_theme = ctk.ThemeManager.theme.get("CTkEntry", {})
        default_border = entry_theme.get("border_color")
        if default_border is not None:
            self.configure(border_color=default_border)
        # Delay để cho phép click vào listbox
        self.after(200, self._check_focus)
    
    def _check_focus(self):
        """Kiểm tra focus sau delay."""
        try:
            focused = self.focus_get()
            if focused != self._listbox and focused != self.entry:
                self._hide_listbox()
        except Exception:
            self._hide_listbox()
    
    def _on_arrow_down(self, event):
        """Xử lý phím mũi tên xuống."""
        if not self._listbox_visible:
            text = self.entry.get()
            if text:
                suggestions = self._get_filtered_suggestions(text)
                self._show_listbox(suggestions)
            return
        
        if self._listbox:
            current = self._listbox.curselection()
            if current:
                idx = current[0]
                if idx < self._listbox.size() - 1:
                    self._listbox.selection_clear(0, END)
                    self._listbox.selection_set(idx + 1)
                    self._listbox.see(idx + 1)
            else:
                self._listbox.selection_set(0)
        return "break"
    
    def _on_arrow_up(self, event):
        """Xử lý phím mũi tên lên."""
        if not self._listbox_visible:
            return
        
        if self._listbox:
            current = self._listbox.curselection()
            if current:
                idx = current[0]
                if idx > 0:
                    self._listbox.selection_clear(0, END)
                    self._listbox.selection_set(idx - 1)
                    self._listbox.see(idx - 1)
        return "break"
    
    def _on_enter(self, event):
        """Xử lý phím Enter."""
        if self._listbox_visible and self._listbox:
            current = self._listbox.curselection()
            if current:
                self._select_item(current[0])
                return "break"
    
    def _on_tab(self, event):
        """Xử lý phím Tab - chọn gợi ý đầu tiên nếu có."""
        if self._listbox_visible and self._listbox and self._listbox.size() > 0:
            self._select_item(0)
    
    def _on_listbox_click(self, event):
        """Xử lý click vào listbox."""
        selection = self._listbox.curselection()
        if selection:
            self._select_item(selection[0])
    
    def _on_listbox_double_click(self, event):
        """Xử lý double click vào listbox."""
        self._on_listbox_click(event)
    
    def _select_item(self, index):
        """Chọn item từ listbox."""
        if self._listbox and index < self._listbox.size():
            value = self._listbox.get(index)
            self.entry.delete(0, END)
            self.entry.insert(0, value)
            self._hide_listbox()
            self.entry.focus_set()
            # Trigger event for external handlers
            self.event_generate("<<AutocompleteSelected>>")
    
    # === Public methods to mimic CTkEntry interface ===
    def get(self):
        """Lấy giá trị từ entry."""
        return self.entry.get()
    
    def set(self, value):
        """Set giá trị cho entry."""
        self.entry.delete(0, END)
        self.entry.insert(0, value)
    
    def delete(self, first, last=None):
        """Xóa text từ entry."""
        self.entry.delete(first, last)
    
    def insert(self, index, string):
        """Insert text vào entry."""
        self.entry.insert(index, string)
    
    def configure(self, **kwargs):
        """Configure entry."""
        if 'suggestions' in kwargs:
            suggestions = kwargs.pop('suggestions')
            if callable(suggestions):
                self._suggestions_func = suggestions
                self._suggestions = []
            else:
                self._suggestions = suggestions
                self._suggestions_func = None
        if kwargs:
            self.entry.configure(**kwargs)
    
    def bind(self, sequence, func, add=None):
        """Bind event to entry."""
        # CTkEntry requires add to be '+' or True, not None
        if add is None:
            return self.entry.bind(sequence, func)
        return self.entry.bind(sequence, func, add)
    
    def focus(self):
        """Set focus to entry."""
        self.entry.focus()
    
    def focus_set(self):
        """Set focus to entry."""
        self.entry.focus_set()
    
    def update_suggestions(self, suggestions):
        """Cập nhật danh sách gợi ý."""
        if callable(suggestions):
            self._suggestions_func = suggestions
            self._suggestions = []
        else:
            self._suggestions = suggestions
            self._suggestions_func = None
# === END PHASE 2.5 ===


def add_right_click_menu(app, widget):
    """Thêm một menu chuột phải (Cắt, Sao chép, Dán) vào một widget."""
    menu = Menu(widget, tearoff=0, font=("Arial", 12))
    
    menu.add_command(label=app.get_translation("ctx_menu_cut"), command=lambda: widget.event_generate("<<Cut>>"))
    menu.add_command(label=app.get_translation("ctx_menu_copy"), command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label=app.get_translation("ctx_menu_paste"), command=lambda: widget.event_generate("<<Paste>>"))
    
    def update_menu_state(event):
        try:
            has_selection = widget.selection_get()
            menu.entryconfigure(app.get_translation("ctx_menu_cut"), state="normal" if has_selection else "disabled")
            menu.entryconfigure(app.get_translation("ctx_menu_copy"), state="normal" if has_selection else "disabled")
        except Exception:
            menu.entryconfigure(app.get_translation("ctx_menu_cut"), state="disabled")
            menu.entryconfigure(app.get_translation("ctx_menu_copy"), state="disabled")
        
        try:
            # Kiểm tra xem clipboard có nội dung không
            widget.clipboard_get()
            menu.entryconfigure(app.get_translation("ctx_menu_paste"), state="normal")
        except Exception:
            menu.entryconfigure(app.get_translation("ctx_menu_paste"), state="disabled")

    def show_menu(event):
        update_menu_state(event)
        menu.tk_popup(event.x_root, event.y_root)

    # Sử dụng bind_class để áp dụng cho cả phần Entry bên trong CTkComboBox
    if isinstance(widget, ctk.CTkComboBox):
        widget._entry.bind("<Button-3>", show_menu)
    else:
        widget.bind("<Button-3>", show_menu)

def style_treeview(app, tree):
    """Áp dụng style của CustomTkinter cho một widget ttk.Treeview."""
    style = ttk.Style()
    
    bg_color = app._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
    text_color = app._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
    selected_color = app._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
    header_bg = app._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["top_fg_color"])
    
    style.theme_use('default')
    style.map('Treeview', background=[('selected', selected_color)], foreground=[('selected', text_color)])
    style.configure("Treeview", background=bg_color, foreground=text_color, fieldbackground=bg_color, rowheight=28, font=("Arial", 12))
    style.configure("Treeview.Heading", background=header_bg, foreground=text_color, font=("Arial", 12, "bold"))
    style.map("Treeview.Heading", relief=[('active','groove'),('!active','flat')])

class Toast:
    """Một thông báo nhỏ, tự động biến mất ở phía trên cửa sổ."""
    def __init__(self, parent, message, duration=2500):
        self.parent = parent
        self.top = Toplevel(parent)
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", True)
        
        bg_color = "#333"
        fg_color = "white"
        
        Label(self.top, text=message, bg=bg_color, fg=fg_color, padx=15, pady=8, font=("Arial", 12, "bold")).pack()
        self.top.update_idletasks()
        
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        
        toast_width = self.top.winfo_width()
        
        x = parent_x + (parent_width // 2) - (toast_width // 2)
        y = parent_y + 50
        
        self.top.geometry(f"+{x}+{y}")
        self.top.after(duration, self.top.destroy)

class DateRangeDialog(ctk.CTkToplevel):
    """Một hộp thoại để chọn khoảng thời gian (Từ ngày - Đến ngày)."""
    def __init__(self, parent, title):
        super().__init__(parent)
        self.transient(parent)
        self.title(title)
        # === SỬA LỖI: Tăng chiều cao của cửa sổ ===
        self.geometry("350x200")
        # ========================================
        self.result = None
        
        self.app = parent.app if hasattr(parent, 'app') else parent

        # === SỬA LỖI: Thêm padding để giao diện thoáng hơn ===
        self.lbl_from = ctk.CTkLabel(self, text=self.app.get_translation("lbl_from_date"), font=self.app.font_normal)
        self.lbl_from.pack(pady=(20, 5)) # Tăng padding ở trên
        self.start_date_entry = DateEntry(self, width=12, date_pattern="dd/mm/yyyy", font=("Arial", 10))
        self.start_date_entry.pack(pady=5)

        self.lbl_to = ctk.CTkLabel(self, text=self.app.get_translation("lbl_to_date"), font=self.app.font_normal)
        self.lbl_to.pack(pady=5)
        self.end_date_entry = DateEntry(self, width=12, date_pattern="dd/mm/yyyy", font=("Arial", 10))
        self.end_date_entry.pack(pady=5)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)
        # =====================================================
        
        ctk.CTkButton(btn_frame, text=self.app.get_translation("btn_ok"), command=self.on_ok, font=self.app.font_normal).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text=self.app.get_translation("btn_cancel"), command=self.destroy, font=self.app.font_normal).pack(side="left", padx=10)
        
        self.grab_set()
        self.wait_window()

    def on_ok(self):
        start_date = datetime.combine(self.start_date_entry.get_date(), datetime.min.time())
        end_date = datetime.combine(self.end_date_entry.get_date(), datetime.max.time())
        self.result = (start_date, end_date)
        self.destroy()

class EditVehicleDialog(ctk.CTkToplevel):
    """Hộp thoại để chỉnh sửa thông tin chi tiết của một chiếc xe."""
    def __init__(self, parent, vehicle_info):
        super().__init__(parent)
        self.transient(parent)
        self.app = parent
        self.title(f"{self.app.get_translation('ctx_menu_edit')}: {vehicle_info['vin']}")
        self.geometry("400x280")
        self.result = None
        self.original_vin = vehicle_info.get('vin', '')

        self.lbl_vin = ctk.CTkLabel(self, text=self.app.get_translation("lbl_vin"), font=self.app.font_normal)
        self.lbl_vin.pack(pady=(10, 0))
        self.vin_entry = ctk.CTkEntry(self, width=300, font=self.app.font_normal)
        self.vin_entry.insert(0, self.original_vin)
        self.vin_entry.pack()
        add_right_click_menu(self.app, self.vin_entry)

        self.lbl_owner = ctk.CTkLabel(self, text=self.app.get_translation("lbl_owner"), font=self.app.font_normal)
        self.lbl_owner.pack(pady=(10, 0))
        self.owner_entry = ctk.CTkEntry(self, width=300, font=self.app.font_normal)
        self.owner_entry.insert(0, vehicle_info.get('owner', ''))
        self.owner_entry.pack()
        add_right_click_menu(self.app, self.owner_entry)

        self.lbl_type = ctk.CTkLabel(self, text=self.app.get_translation("lbl_vehicle_type"), font=self.app.font_normal)
        self.lbl_type.pack(pady=(10, 0))
        self.type_entry = ctk.CTkEntry(self, width=300, font=self.app.font_normal)
        self.type_entry.insert(0, vehicle_info.get('vehicle_type', ''))
        self.type_entry.pack()
        add_right_click_menu(self.app, self.type_entry)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text=self.app.get_translation("btn_save"), command=self.on_ok, font=self.app.font_normal).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text=self.app.get_translation("btn_cancel"), command=self.destroy, font=self.app.font_normal).pack(side="left", padx=10)
        
        self.grab_set()
        self.wait_window()

    def on_ok(self):
        new_vin = self.vin_entry.get().strip().upper()
        if not new_vin:
            messagebox.showwarning(self.app.get_translation("warn_missing_info"), 
                                   self.app.get_translation("warn_field_empty_msg").format(field=self.app.get_translation("lbl_vin")), 
                                   parent=self)
            return

        self.result = {
            "original_vin": self.original_vin,
            "new_vin": new_vin,
            "owner": self.owner_entry.get().strip(),
            "vehicle_type": self.type_entry.get().strip()
        }
        self.destroy()

class LocationSwapDialog(ctk.CTkToplevel):
    """Hộp thoại để di chuyển một xe sang vị trí trống khác."""
    def __init__(self, parent, vehicle_info, location_manager):
        super().__init__(parent)
        self.transient(parent)
        self.app = parent
        self.vehicle_manager = self.app.vehicle_manager
        self.location_manager = location_manager
        
        self.vin = vehicle_info.get('vin')
        self.current_location = vehicle_info.get('full_location_name', 'N/A')
        self.result = None

        self.title(self.app.get_translation("dialog_swap_location_title"))
        self.geometry("450x250")

        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(info_frame, text=f"{self.app.get_translation('lbl_vin')} {self.vin}", font=self.app.font_bold).pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"{self.app.get_translation('lbl_current_location')} {self.current_location}", font=self.app.font_normal).pack(anchor="w")

        swap_frame = ctk.CTkFrame(self, fg_color="transparent")
        swap_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(swap_frame, text=self.app.get_translation("lbl_new_location"), font=self.app.font_normal).pack(anchor="w")
        
        self.location_combo = ctk.CTkComboBox(swap_frame, values=[], font=self.app.font_normal)
        self.location_combo.pack(fill="x", pady=(5,0))
        harmonize_combobox_style(self.location_combo)
        add_right_click_menu(self.app, self.location_combo)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20, padx=20, fill="x")

        ctk.CTkButton(btn_frame, text=self.app.get_translation("btn_confirm"), command=self.on_confirm, font=self.app.font_normal).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text=self.app.get_translation("btn_cancel"), command=self.destroy, font=self.app.font_normal).pack(side="right", expand=True, padx=5)

        self._load_free_locations()
        self.grab_set()
        self.wait_window()

    def _load_free_locations(self):
        free_locations = self.location_manager.get_all_free_locations()
        self.location_map = {loc['full_location_name']: loc['id'] for loc in free_locations}
        self.location_combo.configure(values=list(self.location_map.keys()))
        if self.location_map:
            self.location_combo.set(list(self.location_map.keys())[0])

    def on_confirm(self):
        selected_location_name = self.location_combo.get()
        if not selected_location_name:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn một vị trí mới.", parent=self)
            return
            
        new_location_id = self.location_map.get(selected_location_name)
        
        result = self.vehicle_manager.swap_vehicle_location(self.vin, new_location_id)
        
        if result["success"]:
            self.app.show_toast(result["message"])
            self.result = True
            self.destroy()
        else:
            messagebox.showerror("Lỗi", result["message"], parent=self)


# === PHASE 2.3: Batch Operations Dialog ===
class BatchLocationDialog(ctk.CTkToplevel):
    """Hộp thoại để gán vị trí cho nhiều xe cùng lúc."""
    def __init__(self, parent, vins, location_manager):
        super().__init__(parent)
        self.transient(parent)
        self.app = parent
        self.location_manager = location_manager
        
        self.vins = vins
        self.result = None
        self.auto_assign = False  # Gán tự động từng vị trí cho từng xe

        self.title(self.app.get_translation("batch_assign_location"))
        self.geometry("650x620")
        self.resizable(True, True)
        self.minsize(550, 500)

        # === MAIN CONTENT FRAME ===
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        info_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        info_frame.pack(pady=5, fill="x")
        
        count_text = self.app.get_translation("batch_selected_count").format(count=len(vins))
        ctk.CTkLabel(info_frame, text=count_text, font=self.app.font_bold).pack(anchor="w")
        
        # Show list of VINs (scrollable)
        vin_frame = ctk.CTkFrame(info_frame)
        vin_frame.pack(fill="x", pady=(5, 0))
        
        vin_text = "\n".join(vins[:10])  # Show first 10
        if len(vins) > 10:
            vin_text += f"\n... (+{len(vins) - 10} {self.app.get_translation('batch_more_vehicles')})"
        
        ctk.CTkLabel(vin_frame, text=vin_text, font=self.app.font_normal, justify="left").pack(anchor="w", padx=5, pady=5)

        # === OPTION: Gán tự động hoặc chọn 1 vị trí ===
        option_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        option_frame.pack(pady=10, fill="x")
        
        self.assign_mode = ctk.StringVar(value="auto")
        
        # Radio button: Gán tự động
        self.radio_auto = ctk.CTkRadioButton(
            option_frame, 
            text=self.app.get_translation("batch_auto_assign"),
            variable=self.assign_mode, 
            value="auto",
            font=self.app.font_normal,
            command=self._on_mode_change
        )
        self.radio_auto.pack(anchor="w", pady=2)
        
        # Radio button: Chọn 1 vị trí cụ thể
        self.radio_manual = ctk.CTkRadioButton(
            option_frame, 
            text=self.app.get_translation("batch_manual_assign"),
            variable=self.assign_mode, 
            value="manual",
            font=self.app.font_normal,
            command=self._on_mode_change
        )
        self.radio_manual.pack(anchor="w", pady=2)

        # === BLOCK SELECTION FOR AUTO MODE ===
        self.block_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.block_frame.pack(pady=5, fill="x")
        
        ctk.CTkLabel(self.block_frame, text="📍 Chọn Khu bắt đầu gán:", font=self.app.font_normal).pack(anchor="w")
        
        self.block_var = ctk.StringVar(value="")
        self.block_menu = ctk.CTkOptionMenu(
            self.block_frame,
            variable=self.block_var,
            values=["Tất cả khu"],
            font=self.app.font_normal,
            height=38,
            dynamic_resizing=False,
            command=self._on_block_change
        )
        self.block_menu.pack(fill="x", pady=(5, 0))

        # === LOCATION SELECTION ===
        self.location_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.location_frame.pack(pady=10, fill="x")

        ctk.CTkLabel(self.location_frame, text="📌 Chọn vị trí bắt đầu:", font=self.app.font_normal).pack(anchor="w")
        
        # Sử dụng OptionMenu thay vì ComboBox để dropdown hoạt động tốt hơn
        self.location_var = ctk.StringVar(value="")
        self.location_menu = ctk.CTkOptionMenu(
            self.location_frame, 
            variable=self.location_var,
            values=["Đang tải..."],
            font=self.app.font_normal, 
            height=38,
            dynamic_resizing=False
        )
        self.location_menu.pack(fill="x", pady=(5,0))
        
        # Thông tin vị trí trống
        self.free_count_label = ctk.CTkLabel(
            self.location_frame, 
            text="", 
            font=self.app.font_small,
            text_color="gray"
        )
        self.free_count_label.pack(anchor="w", pady=(5, 0))

        # === BUTTONS - Đặt ở dưới cùng ===
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=20, padx=30, fill="x")

        ctk.CTkButton(
            btn_frame, 
            text="✅ " + self.app.get_translation("btn_confirm"), 
            command=self.on_confirm, 
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#27ae60",
            hover_color="#2ecc71",
            height=45
        ).pack(side="left", expand=True, fill="x", padx=(0, 10))
        
        ctk.CTkButton(
            btn_frame, 
            text="❌ " + self.app.get_translation("btn_cancel"), 
            command=self.destroy, 
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#7f8c8d",
            hover_color="#95a5a6",
            height=45
        ).pack(side="right", expand=True, fill="x", padx=(10, 0))

        self._load_blocks()
        self._load_free_locations()
        self._on_mode_change()  # Set initial state
        
        # Center dialog
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        self.grab_set()
        self.wait_window()

    def _load_blocks(self):
        """Load danh sách các khu có vị trí trống."""
        blocks = self.location_manager.get_all_blocks()
        self.blocks_list = ["Tất cả khu"] + blocks
        self.block_menu.configure(values=self.blocks_list)
        self.block_var.set("Tất cả khu")

    def _on_block_change(self, value):
        """Khi người dùng chọn khu khác."""
        self._load_free_locations()
        self._update_info_label()

    def _on_mode_change(self):
        """Xử lý khi thay đổi chế độ gán."""
        if self.assign_mode.get() == "auto":
            # Enable block selection, enable location to choose starting point
            self.block_menu.configure(state="normal")
            self.location_menu.configure(state="normal")
            self._update_info_label()
        else:
            # Manual mode - only location selection needed
            self.block_menu.configure(state="disabled")
            self.location_menu.configure(state="normal")
            self.free_count_label.configure(
                text=f"⚠️ Tất cả {len(self.vins)} xe sẽ được gán vào CÙNG 1 vị trí",
                text_color="#e67e22"
            )

    def _update_info_label(self):
        """Cập nhật thông tin khi ở chế độ auto."""
        if self.assign_mode.get() == "auto":
            available = len(self.filtered_locations) if hasattr(self, 'filtered_locations') else 0
            if available >= len(self.vins):
                start_loc = self.location_var.get() if self.location_var.get() else "vị trí đầu tiên"
                self.free_count_label.configure(
                    text=f"✅ Sẽ gán {len(self.vins)} xe từ [{start_loc}] trở đi ({available} vị trí trống)",
                    text_color="#27ae60"
                )
            else:
                self.free_count_label.configure(
                    text=f"⚠️ Chỉ có {available} vị trí trống, không đủ cho {len(self.vins)} xe!",
                    text_color="#e74c3c"
                )

    def _load_free_locations(self):
        """Load vị trí trống theo khu đã chọn."""
        selected_block = self.block_var.get()
        
        # Lấy tất cả vị trí trống
        all_free = self.location_manager.get_all_free_locations()
        
        # Lọc theo khu nếu không phải "Tất cả khu"
        if selected_block and selected_block != "Tất cả khu":
            self.filtered_locations = [loc for loc in all_free if loc['full_location_name'].startswith(selected_block)]
        else:
            self.filtered_locations = all_free
        
        self.location_map = {loc['full_location_name']: loc['id'] for loc in self.filtered_locations}
        
        location_names = list(self.location_map.keys())
        if location_names:
            self.location_menu.configure(values=location_names)
            self.location_var.set(location_names[0])
        else:
            self.location_menu.configure(values=["Không có vị trí trống"])
            self.location_var.set("Không có vị trí trống")
        
        self._update_info_label()

    def on_confirm(self):
        if self.assign_mode.get() == "auto":
            # Chế độ tự động: gán từ vị trí đã chọn trở đi
            selected_start = self.location_var.get()
            if not selected_start or selected_start == "Không có vị trí trống":
                messagebox.showwarning(
                    self.app.get_translation("warn_missing_info"),
                    "Vui lòng chọn vị trí bắt đầu!",
                    parent=self
                )
                return
            
            # Tìm index của vị trí bắt đầu
            start_idx = 0
            for i, loc in enumerate(self.filtered_locations):
                if loc['full_location_name'] == selected_start:
                    start_idx = i
                    break
            
            # Lấy các vị trí từ start_idx trở đi
            available_from_start = self.filtered_locations[start_idx:]
            
            if len(available_from_start) < len(self.vins):
                messagebox.showwarning(
                    self.app.get_translation("warn_missing_info"),
                    f"Không đủ vị trí trống! Từ [{selected_start}] chỉ còn {len(available_from_start)} vị trí, cần {len(self.vins)} vị trí.",
                    parent=self
                )
                return
            
            self.result = "auto"
            self.auto_locations = [loc['id'] for loc in available_from_start[:len(self.vins)]]
        else:
            # Chế độ thủ công: trả về 1 location_id
            selected_location_name = self.location_var.get()
            if not selected_location_name or selected_location_name == "Không có vị trí trống":
                messagebox.showwarning(
                    self.app.get_translation("warn_missing_info"),
                    self.app.get_translation("warn_select_location"),
                    parent=self
                )
                return
            self.result = self.location_map.get(selected_location_name)
            self.auto_locations = None
        
        self.destroy()
# === END PHASE 2.3 ===