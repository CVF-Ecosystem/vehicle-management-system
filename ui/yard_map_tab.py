# ui/yard_map_tab.py
"""
Yard Map Tab - Phase 2.2
Tab bản đồ bãi xe 2D với canvas tương tác.
Hiển thị trực quan vị trí xe theo block/row/slot.
"""

import customtkinter as ctk
from tkinter import Canvas, messagebox
import logging
from typing import Dict, List, Optional, Tuple, Callable

from ui.components import harmonize_combobox_style

logger = logging.getLogger(__name__)


class YardMapTab(ctk.CTkFrame):
    """
    Tab hiển thị bản đồ bãi xe dạng 2D.
    - Canvas vẽ các vị trí theo block/row/slot
    - Click vào vị trí để xem thông tin xe
    - Zoom và pan (nếu bãi lớn)
    - Filter theo block, trạng thái
    - Legend màu sắc
    """
    
    # Màu sắc cho các trạng thái
    COLORS = {
        'empty': '#90EE90',        # Xanh lá nhạt - Vị trí trống
        'occupied': '#FFB6C1',     # Hồng nhạt - Có xe
        'selected': '#87CEEB',     # Xanh dương nhạt - Đang chọn
        'hover': '#FFFFE0',        # Vàng nhạt - Hover
        'border': '#333333',       # Viền
        'text': '#000000',         # Text
        'block_header': '#4A90D9', # Header block
    }
    
    # Kích thước slot
    SLOT_WIDTH = 50
    SLOT_HEIGHT = 28
    SLOT_PADDING = 2
    BLOCK_PADDING = 20
    HEADER_HEIGHT = 25
    ROW_LABEL_WIDTH = 35  # Chiều rộng label cho dãy
    
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.app = app
        self._t = app.get_translation
        
        # Managers from app
        self.location_manager = app.location_manager
        self.vehicle_manager = app.vehicle_manager
        
        # Data storage
        self.locations_data: Dict = {}  # {location_id: location_info}
        self.vehicles_data: Dict = {}   # {location_id: vehicle_info}
        self.blocks_layout: Dict = {}   # {block: {rows, slots, x, y}}
        
        # UI state
        self.selected_location: Optional[int] = None
        self.hovered_location: Optional[int] = None
        self.canvas_items: Dict = {}    # {location_id: canvas_item_id}
        
        # Zoom/Pan state
        self.zoom_level = 1.0
        self.pan_offset = (0, 0)
        
        # Build UI
        self._build_ui()
        
        # Pack self
        self.pack(fill="both", expand=True)
        
        # Initial load
        self.after(100, self.refresh_map)
    
    def _build_ui(self):
        """Xây dựng giao diện tab."""
        # Top control panel
        self._build_control_panel()
        
        # Main canvas area
        self._build_canvas_area()
        
        # Bottom info panel
        self._build_info_panel()
        
        # Legend
        self._build_legend()
    
    def _build_control_panel(self):
        """Tạo panel điều khiển ở trên."""
        control_frame = ctk.CTkFrame(self)
        control_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Title
        ctk.CTkLabel(
            control_frame,
            text=f"🗺️ {self._t('yard_map_title')}",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left", padx=10)
        
        # Quick stats label
        self.stats_quick_label = ctk.CTkLabel(
            control_frame,
            text="",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.stats_quick_label.pack(side="left", padx=(10, 20))
        
        # Block filter
        ctk.CTkLabel(
            control_frame,
            text=f"{self._t('yard_map_filter_block')}:"
        ).pack(side="left", padx=(10, 5))
        
        self.block_filter = ctk.CTkComboBox(
            control_frame,
            values=[self._t('yard_map_all_blocks')],
            width=100,
            command=self._on_block_filter_change
        )
        harmonize_combobox_style(self.block_filter)
        self.block_filter.pack(side="left", padx=5)
        self.block_filter.set(self._t('yard_map_all_blocks'))
        
        # Status filter
        ctk.CTkLabel(
            control_frame,
            text=f"{self._t('yard_map_filter_status')}:"
        ).pack(side="left", padx=(10, 5))
        
        self.status_filter = ctk.CTkComboBox(
            control_frame,
            values=[
                self._t('yard_map_all_status'),
                self._t('yard_map_status_empty'),
                self._t('yard_map_status_occupied')
            ],
            width=100,
            command=self._on_status_filter_change
        )
        harmonize_combobox_style(self.status_filter)
        self.status_filter.pack(side="left", padx=5)
        self.status_filter.set(self._t('yard_map_all_status'))
        
        # Zoom controls
        ctk.CTkLabel(control_frame, text="🔍").pack(side="left", padx=(20, 5))
        
        ctk.CTkButton(
            control_frame,
            text="-",
            width=30,
            command=self._zoom_out
        ).pack(side="left", padx=2)
        
        self.zoom_label = ctk.CTkLabel(control_frame, text="100%", width=50)
        self.zoom_label.pack(side="left", padx=5)
        
        ctk.CTkButton(
            control_frame,
            text="+",
            width=30,
            command=self._zoom_in
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            control_frame,
            text="↺",
            width=30,
            command=self._reset_view
        ).pack(side="left", padx=(10, 5))
        
        # Refresh button
        ctk.CTkButton(
            control_frame,
            text=f"🔄 {self._t('btn_refresh')}",
            width=100,
            command=self.refresh_map
        ).pack(side="right", padx=10)
    
    def _build_canvas_area(self):
        """Tạo canvas chính để vẽ bản đồ."""
        canvas_frame = ctk.CTkFrame(self)
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Scrollbars
        h_scroll = ctk.CTkScrollbar(canvas_frame, orientation="horizontal")
        h_scroll.pack(side="bottom", fill="x")
        
        v_scroll = ctk.CTkScrollbar(canvas_frame, orientation="vertical")
        v_scroll.pack(side="right", fill="y")
        
        # Canvas
        self.canvas = Canvas(
            canvas_frame,
            bg='#F5F5F5',
            highlightthickness=0,
            xscrollcommand=h_scroll.set,
            yscrollcommand=v_scroll.set
        )
        self.canvas.pack(side="left", fill="both", expand=True)
        
        h_scroll.configure(command=self.canvas.xview)
        v_scroll.configure(command=self.canvas.yview)
        
        # Bind events
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Motion>", self._on_canvas_hover)
        self.canvas.bind("<Leave>", self._on_canvas_leave)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Button-2>", self._start_pan)  # Middle click
        self.canvas.bind("<B2-Motion>", self._do_pan)
    
    def _build_info_panel(self):
        """Tạo panel thông tin ở dưới."""
        self.info_frame = ctk.CTkFrame(self, height=120)
        self.info_frame.pack(fill="x", padx=10, pady=(5, 10))
        self.info_frame.pack_propagate(False)
        
        # Left side: Location info
        left_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        self.location_info_label = ctk.CTkLabel(
            left_frame,
            text=self._t('yard_map_click_to_view'),
            font=ctk.CTkFont(size=12),
            justify="left",
            anchor="nw"
        )
        self.location_info_label.pack(anchor="nw")
        
        # Right side: Statistics
        right_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        right_frame.pack(side="right", fill="y", padx=10, pady=10)
        
        self.stats_label = ctk.CTkLabel(
            right_frame,
            text="",
            font=ctk.CTkFont(size=11),
            justify="right",
            anchor="ne"
        )
        self.stats_label.pack(anchor="ne")
    
    def _build_legend(self):
        """Tạo legend màu sắc."""
        legend_frame = ctk.CTkFrame(self.info_frame)
        legend_frame.pack(side="bottom", fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            legend_frame,
            text=f"{self._t('yard_map_legend')}:",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="left", padx=5)
        
        # Empty
        self._create_legend_item(legend_frame, self.COLORS['empty'], self._t('yard_map_status_empty'))
        
        # Occupied
        self._create_legend_item(legend_frame, self.COLORS['occupied'], self._t('yard_map_status_occupied'))
        
        # Selected
        self._create_legend_item(legend_frame, self.COLORS['selected'], self._t('yard_map_selected'))
    
    def _create_legend_item(self, parent, color: str, text: str):
        """Tạo một item trong legend."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(side="left", padx=10)
        
        # Color box (using canvas for precise color)
        color_canvas = Canvas(frame, width=16, height=16, highlightthickness=1, highlightbackground='#333')
        color_canvas.pack(side="left", padx=(0, 5))
        color_canvas.create_rectangle(0, 0, 16, 16, fill=color, outline='')
        
        ctk.CTkLabel(frame, text=text, font=ctk.CTkFont(size=10)).pack(side="left")
    
    # ==================== DATA LOADING ====================
    
    def refresh_map(self):
        """Làm mới dữ liệu và vẽ lại bản đồ."""
        try:
            # Load locations
            self._load_locations_data()
            
            # Load vehicles at locations
            self._load_vehicles_data()
            
            # Update block filter options
            self._update_block_filter()
            
            # Redraw canvas
            self._draw_map()
            
            # Update statistics
            self._update_statistics()
            
            logger.info("Yard map refreshed successfully")
            
        except Exception as e:
            logger.error(f"Error refreshing yard map: {e}")
            messagebox.showerror(
                self._t('dialog_error_title'),
                f"{self._t('yard_map_load_error')}: {e}"
            )
    
    def _load_locations_data(self):
        """Load dữ liệu vị trí từ database."""
        self.locations_data.clear()
        self.blocks_layout.clear()
        
        try:
            # Get all locations using location_manager
            cursor = self.location_manager.conn.cursor()
            cursor.execute("""
                SELECT id, block, row, slot, full_location_name, is_occupied
                FROM locations
                ORDER BY block, row, slot
            """)
            
            for row in cursor.fetchall():
                loc = dict(row)
                self.locations_data[loc['id']] = loc
                
                # Build blocks layout
                block = loc['block']
                if block not in self.blocks_layout:
                    self.blocks_layout[block] = {
                        'rows': set(),
                        'slots': set(),
                        'locations': []
                    }
                
                self.blocks_layout[block]['rows'].add(loc['row'])
                self.blocks_layout[block]['slots'].add(loc['slot'])
                self.blocks_layout[block]['locations'].append(loc['id'])
                
        except Exception as e:
            logger.error(f"Error loading locations: {e}")
            raise
    
    def _load_vehicles_data(self):
        """Load dữ liệu xe đang tồn tại vị trí."""
        self.vehicles_data.clear()
        
        try:
            # Get vehicles with location using vehicle_manager
            cursor = self.vehicle_manager.conn.cursor()
            cursor.execute("""
                SELECT v.vin, v.owner, v.vehicle_type, v.location_id,
                       v.date_in, l.full_location_name
                FROM vehicles v
                INNER JOIN locations l ON v.location_id = l.id
                WHERE UPPER(v.status) = 'IN_STOCK' AND (v.is_deleted = 0 OR v.is_deleted IS NULL)
            """)
            
            for row in cursor.fetchall():
                vehicle = dict(row)
                self.vehicles_data[vehicle['location_id']] = vehicle
                
        except Exception as e:
            logger.error(f"Error loading vehicles: {e}")
            raise
    
    def _update_block_filter(self):
        """Cập nhật danh sách blocks trong filter."""
        blocks = sorted(self.blocks_layout.keys())
        values = [self._t('yard_map_all_blocks')] + blocks
        self.block_filter.configure(values=values)
    
    # ==================== DRAWING ====================
    
    def _draw_map(self):
        """Vẽ toàn bộ bản đồ."""
        # Clear canvas
        self.canvas.delete("all")
        self.canvas_items.clear()
        
        if not self.blocks_layout:
            # No data
            self.canvas.create_text(
                300, 200,
                text=self._t('yard_map_no_data'),
                font=('Arial', 14),
                fill='#666'
            )
            return
        
        # Get filter values
        selected_block = self.block_filter.get()
        selected_status = self.status_filter.get()
        
        # Calculate positions for each block
        x_offset = self.BLOCK_PADDING
        y_offset = self.BLOCK_PADDING
        max_height = 0
        
        sorted_blocks = sorted(self.blocks_layout.keys())
        
        for block in sorted_blocks:
            # Skip if filtered
            if selected_block != self._t('yard_map_all_blocks') and block != selected_block:
                continue
            
            layout = self.blocks_layout[block]
            
            # Calculate block size - thêm label dãy vào chiều rộng
            rows = sorted(layout['rows'], key=lambda r: int(r) if r.isdigit() else r)
            slots = sorted(layout['slots'], key=lambda s: int(s) if isinstance(s, (int, str)) and str(s).isdigit() else s)
            
            block_width = self.ROW_LABEL_WIDTH + len(slots) * (self.SLOT_WIDTH + self.SLOT_PADDING) + self.BLOCK_PADDING
            block_height = len(rows) * (self.SLOT_HEIGHT + self.SLOT_PADDING) + self.HEADER_HEIGHT + self.BLOCK_PADDING
            
            # Check if block fits in current row
            canvas_width = self.canvas.winfo_width() or 800
            if x_offset + block_width > canvas_width - self.BLOCK_PADDING and x_offset > self.BLOCK_PADDING:
                x_offset = self.BLOCK_PADDING
                y_offset += max_height + self.BLOCK_PADDING
                max_height = 0
            
            # Draw block
            self._draw_block(block, x_offset, y_offset, rows, slots, selected_status)
            
            x_offset += block_width + self.BLOCK_PADDING
            max_height = max(max_height, block_height)
        
        # Update scroll region
        total_width = max(x_offset, 800)
        total_height = max(y_offset + max_height + self.BLOCK_PADDING, 400)
        self.canvas.configure(scrollregion=(0, 0, total_width, total_height))
    
    def _draw_block(self, block: str, x: int, y: int, rows: List, slots: List, status_filter: str):
        """Vẽ một block - luôn hiển thị dạng grid với dãy (row) theo chiều dọc, vị trí (slot) theo chiều ngang."""
        # Sắp xếp rows và slots theo số tự nhiên
        rows = sorted(rows, key=lambda r: int(r) if r.isdigit() else r)
        slots = sorted(slots, key=lambda s: int(s) if isinstance(s, (int, str)) and str(s).isdigit() else s)
        
        # Chiều rộng block = label dãy + (số slot * chiều rộng slot)
        block_width = self.ROW_LABEL_WIDTH + len(slots) * (self.SLOT_WIDTH + self.SLOT_PADDING)
        block_height = len(rows) * (self.SLOT_HEIGHT + self.SLOT_PADDING) + self.HEADER_HEIGHT
        
        # Draw block header (tên khu)
        self.canvas.create_rectangle(
            x, y, x + block_width, y + self.HEADER_HEIGHT,
            fill=self.COLORS['block_header'],
            outline=self.COLORS['border']
        )
        self.canvas.create_text(
            x + block_width / 2, y + self.HEADER_HEIGHT / 2,
            text=f"Khu {block}",
            font=('Arial', 10, 'bold'),
            fill='white'
        )
        
        # Draw slots grid
        y_start = y + self.HEADER_HEIGHT + self.SLOT_PADDING
        
        for row_idx, row in enumerate(rows):
            # Draw row label (tên dãy)
            row_y = y_start + row_idx * (self.SLOT_HEIGHT + self.SLOT_PADDING)
            self.canvas.create_text(
                x + self.ROW_LABEL_WIDTH / 2,
                row_y + self.SLOT_HEIGHT / 2,
                text=f"{row}",
                font=('Arial', 8, 'bold'),
                fill='#555'
            )
            
            for slot_idx, slot in enumerate(slots):
                # Find location
                location = self._find_location(block, row, slot)
                if not location:
                    continue
                
                loc_id = location['id']
                is_occupied = loc_id in self.vehicles_data
                
                # Apply status filter
                if status_filter == self._t('yard_map_status_empty') and is_occupied:
                    continue
                if status_filter == self._t('yard_map_status_occupied') and not is_occupied:
                    continue
                
                # Calculate slot position (sau label dãy)
                slot_x = x + self.ROW_LABEL_WIDTH + slot_idx * (self.SLOT_WIDTH + self.SLOT_PADDING)
                slot_y = row_y
                
                # Draw slot
                self._draw_slot(loc_id, slot_x, slot_y, is_occupied, location)
    
    def _draw_slot(self, loc_id: int, x: int, y: int, is_occupied: bool, location: dict):
        """Vẽ một slot."""
        # Determine color
        if loc_id == self.selected_location:
            fill_color = self.COLORS['selected']
        elif loc_id == self.hovered_location:
            fill_color = self.COLORS['hover']
        elif is_occupied:
            fill_color = self.COLORS['occupied']
        else:
            fill_color = self.COLORS['empty']
        
        # Draw rectangle
        rect_id = self.canvas.create_rectangle(
            x, y,
            x + self.SLOT_WIDTH, y + self.SLOT_HEIGHT,
            fill=fill_color,
            outline=self.COLORS['border'],
            width=1,
            tags=('slot', f'loc_{loc_id}')
        )
        
        # Draw slot label - chỉ hiện số vị trí
        label = f"{location['slot']}"
        text_id = self.canvas.create_text(
            x + self.SLOT_WIDTH / 2,
            y + self.SLOT_HEIGHT / 2,
            text=label,
            font=('Arial', 8),
            fill=self.COLORS['text'],
            tags=('slot_text', f'loc_{loc_id}')
        )
        
        # Store reference
        self.canvas_items[loc_id] = (rect_id, text_id, x, y)
    
    def _find_location(self, block: str, row: str, slot) -> Optional[dict]:
        """Tìm location theo block/row/slot."""
        # Chuyển đổi slot về int để so sánh đúng
        slot_int = int(slot) if isinstance(slot, str) and slot.isdigit() else slot
        
        for loc_id, loc in self.locations_data.items():
            loc_slot = int(loc['slot']) if isinstance(loc['slot'], str) and str(loc['slot']).isdigit() else loc['slot']
            if loc['block'] == block and loc['row'] == row and loc_slot == slot_int:
                return loc
        return None
    
    # ==================== EVENT HANDLERS ====================
    
    def _on_canvas_click(self, event):
        """Xử lý click trên canvas."""
        # Find clicked item
        items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        
        for item in items:
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith('loc_'):
                    loc_id = int(tag.split('_')[1])
                    self._select_location(loc_id)
                    return
        
        # Clicked on empty area - deselect
        self._select_location(None)
    
    def _on_canvas_hover(self, event):
        """Xử lý hover trên canvas."""
        items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        
        new_hover = None
        for item in items:
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith('loc_'):
                    new_hover = int(tag.split('_')[1])
                    break
            if new_hover:
                break
        
        if new_hover != self.hovered_location:
            old_hover = self.hovered_location
            self.hovered_location = new_hover
            
            # Update visuals
            if old_hover and old_hover in self.canvas_items:
                self._update_slot_color(old_hover)
            if new_hover and new_hover in self.canvas_items:
                self._update_slot_color(new_hover)
    
    def _on_canvas_leave(self, event):
        """Xử lý khi chuột rời canvas."""
        if self.hovered_location:
            old_hover = self.hovered_location
            self.hovered_location = None
            if old_hover in self.canvas_items:
                self._update_slot_color(old_hover)
    
    def _select_location(self, loc_id: Optional[int]):
        """Chọn một vị trí."""
        old_selected = self.selected_location
        self.selected_location = loc_id
        
        # Update visuals
        if old_selected and old_selected in self.canvas_items:
            self._update_slot_color(old_selected)
        if loc_id and loc_id in self.canvas_items:
            self._update_slot_color(loc_id)
        
        # Update info panel
        self._update_info_panel()
    
    def _update_slot_color(self, loc_id: int):
        """Cập nhật màu slot."""
        if loc_id not in self.canvas_items:
            return
        
        rect_id, text_id, x, y = self.canvas_items[loc_id]
        is_occupied = loc_id in self.vehicles_data
        
        if loc_id == self.selected_location:
            fill_color = self.COLORS['selected']
        elif loc_id == self.hovered_location:
            fill_color = self.COLORS['hover']
        elif is_occupied:
            fill_color = self.COLORS['occupied']
        else:
            fill_color = self.COLORS['empty']
        
        self.canvas.itemconfig(rect_id, fill=fill_color)
    
    def _update_info_panel(self):
        """Cập nhật panel thông tin."""
        if not self.selected_location:
            self.location_info_label.configure(text=self._t('yard_map_click_to_view'))
            return
        
        loc = self.locations_data.get(self.selected_location)
        if not loc:
            return
        
        # Build info text - sử dụng tên chuẩn Khu/Dãy/Vị trí
        info_lines = [
            f"📍 {self._t('yard_map_location')}: {loc['full_location_name']}",
            f"🏗️ Khu: {loc['block']} | Dãy: {loc['row']} | Vị trí: {loc['slot']}"
        ]
        
        vehicle = self.vehicles_data.get(self.selected_location)
        if vehicle:
            info_lines.append("")
            info_lines.append(f"🚗 VIN: {vehicle['vin']}")
            info_lines.append(f"👤 {self._t('lbl_owner')}: {vehicle['owner']}")
            if vehicle.get('vehicle_type'):
                info_lines.append(f"📋 {self._t('lbl_vehicle_type')}: {vehicle['vehicle_type']}")
            # Format date nicely
            date_in = vehicle.get('date_in', '')
            if date_in:
                try:
                    from datetime import datetime
                    if 'T' in date_in:
                        dt = datetime.fromisoformat(date_in.split('.')[0])
                    else:
                        dt = datetime.strptime(date_in, '%Y-%m-%d %H:%M:%S')
                    date_in = dt.strftime('%d/%m/%Y %H:%M')
                except:
                    pass
            info_lines.append(f"📅 {self._t('tree_date_in')}: {date_in}")
        else:
            info_lines.append("")
            info_lines.append(f"✅ {self._t('yard_map_slot_empty')}")
        
        self.location_info_label.configure(text="\n".join(info_lines))
    
    def _update_statistics(self):
        """Cập nhật thống kê."""
        total_locations = len(self.locations_data)
        occupied = len(self.vehicles_data)
        empty = total_locations - occupied
        utilization = (occupied / total_locations * 100) if total_locations > 0 else 0
        
        # Quick stats in control panel
        quick_stats = f"📊 {occupied}/{total_locations} ({utilization:.0f}%)"
        self.stats_quick_label.configure(text=quick_stats)
        
        # Detailed stats in info panel
        stats_text = f"""📊 {self._t('yard_map_statistics')}:
{self._t('yard_map_total_slots')}: {total_locations}
{self._t('yard_map_occupied')}: {occupied}
{self._t('yard_map_empty')}: {empty}
{self._t('yard_map_utilization')}: {utilization:.1f}%"""
        
        self.stats_label.configure(text=stats_text)
    
    # ==================== FILTER HANDLERS ====================
    
    def _on_block_filter_change(self, value):
        """Xử lý khi thay đổi filter block."""
        self._draw_map()
    
    def _on_status_filter_change(self, value):
        """Xử lý khi thay đổi filter status."""
        self._draw_map()
    
    # ==================== ZOOM/PAN ====================
    
    def _zoom_in(self):
        """Phóng to."""
        if self.zoom_level < 2.0:
            self.zoom_level += 0.1
            self._apply_zoom()
    
    def _zoom_out(self):
        """Thu nhỏ."""
        if self.zoom_level > 0.5:
            self.zoom_level -= 0.1
            self._apply_zoom()
    
    def _reset_view(self):
        """Reset về zoom và vị trí mặc định."""
        self.zoom_level = 1.0
        self.pan_offset = (0, 0)
        self._apply_zoom()
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
    
    def _apply_zoom(self):
        """Áp dụng zoom level."""
        self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
        
        # Scale canvas items
        self.SLOT_WIDTH = int(60 * self.zoom_level)
        self.SLOT_HEIGHT = int(30 * self.zoom_level)
        
        self._draw_map()
    
    def _on_mouse_wheel(self, event):
        """Xử lý cuộn chuột (zoom)."""
        if event.delta > 0:
            self._zoom_in()
        else:
            self._zoom_out()
    
    def _start_pan(self, event):
        """Bắt đầu pan."""
        self.canvas.scan_mark(event.x, event.y)
    
    def _do_pan(self, event):
        """Thực hiện pan."""
        self.canvas.scan_dragto(event.x, event.y, gain=1)
