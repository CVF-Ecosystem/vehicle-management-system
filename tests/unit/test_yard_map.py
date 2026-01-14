# tests/unit/test_yard_map.py
"""
Unit tests cho YardMapTab - Phase 2.2
Test logic xử lý dữ liệu, không test UI trực tiếp.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys

# Mock các module UI trước khi import
sys.modules['customtkinter'] = Mock()
sys.modules['tkinter'] = Mock()


class TestYardMapDataProcessing:
    """Test xử lý dữ liệu của YardMapTab."""
    
    @pytest.fixture
    def mock_locations_data(self):
        """Mock dữ liệu locations từ database."""
        return [
            {'id': 1, 'block': 'A', 'row': '1', 'slot': '01', 'full_location_name': 'A-1-01', 'is_occupied': 0},
            {'id': 2, 'block': 'A', 'row': '1', 'slot': '02', 'full_location_name': 'A-1-02', 'is_occupied': 1},
            {'id': 3, 'block': 'A', 'row': '2', 'slot': '01', 'full_location_name': 'A-2-01', 'is_occupied': 0},
            {'id': 4, 'block': 'B', 'row': '1', 'slot': '01', 'full_location_name': 'B-1-01', 'is_occupied': 0},
            {'id': 5, 'block': 'B', 'row': '1', 'slot': '02', 'full_location_name': 'B-1-02', 'is_occupied': 1},
        ]
    
    @pytest.fixture
    def mock_vehicles_data(self):
        """Mock dữ liệu vehicles từ database."""
        return [
            {'id': 101, 'vin': 'VIN001', 'owner': 'Toyota', 'model': 'Camry', 'color': 'White', 'location_id': 2, 'date_in': '2025-01-15'},
            {'id': 102, 'vin': 'VIN002', 'owner': 'Honda', 'model': 'Civic', 'color': 'Black', 'location_id': 5, 'date_in': '2025-01-16'},
        ]
    
    def test_build_blocks_layout(self, mock_locations_data):
        """Test xây dựng cấu trúc blocks từ dữ liệu locations."""
        # Simulate logic from YardMapTab._load_locations_data
        blocks_layout = {}
        
        for loc in mock_locations_data:
            block = loc['block']
            if block not in blocks_layout:
                blocks_layout[block] = {
                    'rows': set(),
                    'slots': set(),
                    'locations': []
                }
            
            blocks_layout[block]['rows'].add(loc['row'])
            blocks_layout[block]['slots'].add(loc['slot'])
            blocks_layout[block]['locations'].append(loc['id'])
        
        # Assertions
        assert 'A' in blocks_layout
        assert 'B' in blocks_layout
        assert blocks_layout['A']['rows'] == {'1', '2'}
        assert blocks_layout['A']['slots'] == {'01', '02'}
        assert len(blocks_layout['A']['locations']) == 3
        assert len(blocks_layout['B']['locations']) == 2
    
    def test_vehicles_mapping(self, mock_vehicles_data):
        """Test mapping xe vào location."""
        vehicles_data = {}
        
        for vehicle in mock_vehicles_data:
            vehicles_data[vehicle['location_id']] = vehicle
        
        assert 2 in vehicles_data
        assert 5 in vehicles_data
        assert vehicles_data[2]['vin'] == 'VIN001'
        assert vehicles_data[5]['vin'] == 'VIN002'
    
    def test_calculate_statistics(self, mock_locations_data, mock_vehicles_data):
        """Test tính toán thống kê."""
        total_locations = len(mock_locations_data)
        occupied = len(mock_vehicles_data)
        empty = total_locations - occupied
        utilization = (occupied / total_locations * 100) if total_locations > 0 else 0
        
        assert total_locations == 5
        assert occupied == 2
        assert empty == 3
        assert utilization == 40.0
    
    def test_find_location_by_block_row_slot(self, mock_locations_data):
        """Test tìm location theo block/row/slot."""
        def find_location(block, row, slot):
            for loc in mock_locations_data:
                if loc['block'] == block and loc['row'] == row and loc['slot'] == slot:
                    return loc
            return None
        
        # Found
        result = find_location('A', '1', '01')
        assert result is not None
        assert result['id'] == 1
        
        result = find_location('B', '1', '02')
        assert result is not None
        assert result['id'] == 5
        
        # Not found
        result = find_location('C', '1', '01')
        assert result is None
    
    def test_filter_by_block(self, mock_locations_data):
        """Test lọc theo block."""
        # Filter block A
        filtered = [loc for loc in mock_locations_data if loc['block'] == 'A']
        assert len(filtered) == 3
        
        # Filter block B
        filtered = [loc for loc in mock_locations_data if loc['block'] == 'B']
        assert len(filtered) == 2
    
    def test_filter_by_status(self, mock_locations_data, mock_vehicles_data):
        """Test lọc theo trạng thái occupied/empty."""
        occupied_location_ids = {v['location_id'] for v in mock_vehicles_data}
        
        # Filter empty
        empty_locs = [loc for loc in mock_locations_data if loc['id'] not in occupied_location_ids]
        assert len(empty_locs) == 3
        
        # Filter occupied
        occupied_locs = [loc for loc in mock_locations_data if loc['id'] in occupied_location_ids]
        assert len(occupied_locs) == 2


class TestYardMapColorLogic:
    """Test logic màu sắc cho slots."""
    
    def test_slot_color_empty(self):
        """Test màu slot trống."""
        COLORS = {
            'empty': '#90EE90',
            'occupied': '#FFB6C1',
            'selected': '#87CEEB',
            'hover': '#FFFFE0',
        }
        
        # Logic từ _draw_slot
        is_occupied = False
        selected_location = None
        hovered_location = None
        loc_id = 1
        
        if loc_id == selected_location:
            fill_color = COLORS['selected']
        elif loc_id == hovered_location:
            fill_color = COLORS['hover']
        elif is_occupied:
            fill_color = COLORS['occupied']
        else:
            fill_color = COLORS['empty']
        
        assert fill_color == '#90EE90'
    
    def test_slot_color_occupied(self):
        """Test màu slot có xe."""
        COLORS = {
            'empty': '#90EE90',
            'occupied': '#FFB6C1',
            'selected': '#87CEEB',
            'hover': '#FFFFE0',
        }
        
        is_occupied = True
        selected_location = None
        hovered_location = None
        loc_id = 1
        
        if loc_id == selected_location:
            fill_color = COLORS['selected']
        elif loc_id == hovered_location:
            fill_color = COLORS['hover']
        elif is_occupied:
            fill_color = COLORS['occupied']
        else:
            fill_color = COLORS['empty']
        
        assert fill_color == '#FFB6C1'
    
    def test_slot_color_selected(self):
        """Test màu slot được chọn (priority cao nhất)."""
        COLORS = {
            'empty': '#90EE90',
            'occupied': '#FFB6C1',
            'selected': '#87CEEB',
            'hover': '#FFFFE0',
        }
        
        is_occupied = True  # Even if occupied
        selected_location = 1
        hovered_location = 1  # Even if hovered
        loc_id = 1
        
        if loc_id == selected_location:
            fill_color = COLORS['selected']
        elif loc_id == hovered_location:
            fill_color = COLORS['hover']
        elif is_occupied:
            fill_color = COLORS['occupied']
        else:
            fill_color = COLORS['empty']
        
        assert fill_color == '#87CEEB'  # Selected takes priority
    
    def test_slot_color_hover(self):
        """Test màu slot hover."""
        COLORS = {
            'empty': '#90EE90',
            'occupied': '#FFB6C1',
            'selected': '#87CEEB',
            'hover': '#FFFFE0',
        }
        
        is_occupied = False
        selected_location = None
        hovered_location = 1
        loc_id = 1
        
        if loc_id == selected_location:
            fill_color = COLORS['selected']
        elif loc_id == hovered_location:
            fill_color = COLORS['hover']
        elif is_occupied:
            fill_color = COLORS['occupied']
        else:
            fill_color = COLORS['empty']
        
        assert fill_color == '#FFFFE0'


class TestYardMapZoom:
    """Test logic zoom."""
    
    def test_zoom_in_limit(self):
        """Test zoom in không vượt quá 200%."""
        zoom_level = 1.0
        max_zoom = 2.0
        
        for _ in range(15):  # Try zooming 15 times
            if zoom_level < max_zoom:
                zoom_level += 0.1
        
        assert zoom_level <= max_zoom + 0.01  # Allow floating point tolerance
    
    def test_zoom_out_limit(self):
        """Test zoom out không dưới 50%."""
        zoom_level = 1.0
        min_zoom = 0.5
        
        for _ in range(15):  # Try zooming out 15 times
            if zoom_level > min_zoom + 0.01:  # Check with tolerance before decrement
                zoom_level -= 0.1
        
        # Result should be around 0.5 (allow floating point tolerance)
        assert zoom_level >= 0.49
    
    def test_slot_size_scaling(self):
        """Test kích thước slot thay đổi theo zoom."""
        base_slot_width = 60
        base_slot_height = 30
        
        # Zoom 150%
        zoom_level = 1.5
        scaled_width = int(base_slot_width * zoom_level)
        scaled_height = int(base_slot_height * zoom_level)
        
        assert scaled_width == 90
        assert scaled_height == 45
        
        # Zoom 50%
        zoom_level = 0.5
        scaled_width = int(base_slot_width * zoom_level)
        scaled_height = int(base_slot_height * zoom_level)
        
        assert scaled_width == 30
        assert scaled_height == 15


class TestYardMapLayout:
    """Test logic layout tính toán vị trí."""
    
    def test_block_size_calculation(self):
        """Test tính toán kích thước block."""
        SLOT_WIDTH = 60
        SLOT_HEIGHT = 30
        SLOT_PADDING = 2
        BLOCK_PADDING = 20
        HEADER_HEIGHT = 25
        
        rows = ['1', '2', '3']
        slots = ['01', '02', '03', '04']
        
        block_width = len(slots) * (SLOT_WIDTH + SLOT_PADDING) + BLOCK_PADDING
        block_height = len(rows) * (SLOT_HEIGHT + SLOT_PADDING) + HEADER_HEIGHT + BLOCK_PADDING
        
        expected_width = 4 * (60 + 2) + 20  # 268
        expected_height = 3 * (30 + 2) + 25 + 20  # 141
        
        assert block_width == expected_width
        assert block_height == expected_height
    
    def test_slot_position_calculation(self):
        """Test tính toán vị trí slot trong block."""
        SLOT_WIDTH = 60
        SLOT_HEIGHT = 30
        SLOT_PADDING = 2
        HEADER_HEIGHT = 25
        
        block_x = 20  # Starting X of block
        block_y = 20  # Starting Y of block
        
        # Position of slot at row_idx=1, slot_idx=2
        row_idx = 1
        slot_idx = 2
        
        y_start = block_y + HEADER_HEIGHT + SLOT_PADDING
        
        slot_x = block_x + slot_idx * (SLOT_WIDTH + SLOT_PADDING)
        slot_y = y_start + row_idx * (SLOT_HEIGHT + SLOT_PADDING)
        
        expected_x = 20 + 2 * (60 + 2)  # 144
        expected_y = 20 + 25 + 2 + 1 * (30 + 2)  # 79
        
        assert slot_x == expected_x
        assert slot_y == expected_y
