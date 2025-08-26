"""
Export Engine for Simplified Paleo Labels
Optimized PDF generation with multi-label sheet support and style integration.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from io import BytesIO
import polars as pl
from datetime import datetime
import tomli
from pathlib import Path

from simple_storage import SimpleStorage


class ExportEngine:
    """Optimized export engine for PDF generation and data export."""
    
    def __init__(self, storage: SimpleStorage):
        self.storage = storage
        
        # Standard label templates with dimensions in points (72 points = 1 inch)
        self.label_templates = {
            'Standard': {
                'page_size': letter,
                'label_width': 4 * inch,
                'label_height': 2 * inch,
                'labels_per_row': 2,
                'labels_per_col': 5,
                'margin_left': 0.5 * inch,
                'margin_top': 0.5 * inch,
                'margin_right': 0.5 * inch,
                'margin_bottom': 0.5 * inch
            },
            'Avery 5160': {
                'page_size': letter,
                'label_width': 2.625 * inch,
                'label_height': 1 * inch,
                'labels_per_row': 3,
                'labels_per_col': 10,
                'margin_left': 0.1875 * inch,
                'margin_top': 0.5 * inch,
                'margin_right': 0.1875 * inch,
                'margin_bottom': 0.5 * inch
            },
            'Avery 8160': {
                'page_size': letter,
                'label_width': 2.625 * inch,
                'label_height': 1 * inch,
                'labels_per_row': 3,
                'labels_per_col': 10,
                'margin_left': 0.15625 * inch,
                'margin_top': 0.5 * inch,
                'margin_right': 0.15625 * inch,
                'margin_bottom': 0.5 * inch
            }
        }
        
        # Default style configuration
        self.default_style = {
            'font_family': 'Helvetica',
            'font_size': 10,
            'title_font_size': 12,
            'line_height': 1.2,
            'text_color': colors.black,
            'background_color': colors.white,
            'border_width': 0.5,
            'border_color': colors.black,
            'padding': 4
        }
    
    def create_single_label_pdf(self, label_data: dict[str, str], style_data: str = None, 
                               template_name: str = "Standard") -> bytes:
        """Create a single label PDF."""
        buffer = BytesIO()
        
        # Parse style if provided
        style_config = self._parse_style_config(style_data)
        template = self.label_templates.get(template_name, self.label_templates['Standard'])
        
        # Create canvas
        c = canvas.Canvas(buffer, pagesize=template['page_size'])
        
        # Draw single label
        x = template['margin_left']
        y = template['page_size'][1] - template['margin_top'] - template['label_height']
        
        self._draw_label(c, label_data, x, y, template, style_config)
        
        c.save()
        return buffer.getvalue()
    
    def create_multi_label_sheet(self, labels_data: list[dict[str, str]], 
                                style_data: str = None, template_name: str = "Standard") -> bytes:
        """Create optimized multi-label sheet PDF."""
        buffer = BytesIO()
        
        # Parse style if provided
        style_config = self._parse_style_config(style_data)
        template = self.label_templates.get(template_name, self.label_templates['Standard'])
        
        # Create canvas
        c = canvas.Canvas(buffer, pagesize=template['page_size'])
        
        labels_per_page = template['labels_per_row'] * template['labels_per_col']
        current_label = 0
        
        for page_labels in self._chunk_labels(labels_data, labels_per_page):
            if current_label > 0:  # New page after first
                c.showPage()
            
            # Draw labels on current page
            for i, label_data in enumerate(page_labels):
                row = i // template['labels_per_row']
                col = i % template['labels_per_row']
                
                x = template['margin_left'] + col * (template['label_width'] + template.get('spacing_x', 0))
                y = (template['page_size'][1] - template['margin_top'] - 
                     template['label_height'] - row * (template['label_height'] + template.get('spacing_y', 0)))
                
                self._draw_label(c, label_data, x, y, template, style_config)
            
            current_label += len(page_labels)
        
        c.save()
        return buffer.getvalue()
    
    def _draw_label(self, canvas: canvas.Canvas, label_data: dict[str, str], 
                   x: float, y: float, template: dict, style_config: dict):
        """Draw a single label on the canvas."""
        label_width = template['label_width']
        label_height = template['label_height']
        
        # Draw border if specified
        if style_config.get('border_width', 0) > 0:
            canvas.setStrokeColor(style_config.get('border_color', colors.black))
            canvas.setLineWidth(style_config.get('border_width', 0.5))
            canvas.rect(x, y, label_width, label_height)
        
        # Fill background if specified
        bg_color = style_config.get('background_color')
        if bg_color and bg_color != colors.white:
            canvas.setFillColor(bg_color)
            canvas.rect(x, y, label_width, label_height, fill=1, stroke=0)
        
        # Set text properties
        canvas.setFillColor(style_config.get('text_color', colors.black))
        font_family = style_config.get('font_family', 'Helvetica')
        font_size = style_config.get('font_size', 10)
        padding = style_config.get('padding', 4)
        
        # Calculate text area
        text_x = x + padding
        text_y = y + label_height - padding - font_size
        text_width = label_width - 2 * padding
        text_height = label_height - 2 * padding
        
        # Draw label content
        current_y = text_y
        line_height = font_size * style_config.get('line_height', 1.2)
        
        for key, value in label_data.items():
            if current_y < y + padding:  # Check if we're running out of space
                break
            
            # Format field
            if value.strip():
                text = f"{key}: {value}"
            else:
                text = f"{key}: _______________"  # Blank line for empty values
            
            # Handle long text wrapping
            wrapped_lines = self._wrap_text(text, text_width, font_family, font_size)
            
            for line in wrapped_lines:
                if current_y < y + padding:
                    break
                
                canvas.setFont(font_family, font_size)
                canvas.drawString(text_x, current_y, line)
                current_y -= line_height
    
    def _wrap_text(self, text: str, max_width: float, font_family: str, font_size: int) -> list[str]:
        """Wrap text to fit within specified width."""
        # Simple word wrapping - could be enhanced with more sophisticated algorithms
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            # Approximate character width (this could be more precise)
            char_width = font_size * 0.6  # Rough approximation
            
            if len(test_line) * char_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines or ['']
    
    def _chunk_labels(self, labels_data: list[dict[str, str]], chunk_size: int) -> list[list[dict[str, str]]]:
        """Split labels into chunks for multi-page processing."""
        for i in range(0, len(labels_data), chunk_size):
            yield labels_data[i:i + chunk_size]
    
    def _parse_style_config(self, style_data: str = None) -> dict:
        """Parse TOML style configuration."""
        style_config = self.default_style.copy()
        
        if style_data:
            try:
                parsed_style = tomli.loads(style_data)
                
                # Map TOML style to internal format
                if 'label_style' in parsed_style:
                    label_style = parsed_style['label_style']
                    
                    # Font settings
                    if 'font_family' in label_style:
                        style_config['font_family'] = label_style['font_family']
                    if 'font_size' in label_style:
                        style_config['font_size'] = label_style['font_size']
                    if 'title_font_size' in label_style:
                        style_config['title_font_size'] = label_style['title_font_size']
                    
                    # Colors
                    if 'text_color' in label_style:
                        style_config['text_color'] = self._parse_color(label_style['text_color'])
                    if 'background_color' in label_style:
                        style_config['background_color'] = self._parse_color(label_style['background_color'])
                    if 'border_color' in label_style:
                        style_config['border_color'] = self._parse_color(label_style['border_color'])
                    
                    # Layout
                    if 'border_width' in label_style:
                        style_config['border_width'] = label_style['border_width']
                    if 'padding' in label_style:
                        style_config['padding'] = label_style['padding']
                    if 'line_height' in label_style:
                        style_config['line_height'] = label_style['line_height']
                
            except Exception as e:
                print(f"Error parsing style config: {e}")
        
        return style_config
    
    def _parse_color(self, color_value) -> colors.Color:
        """Parse color value from style config."""
        if isinstance(color_value, str):
            if color_value.startswith('#'):
                # Hex color
                return colors.HexColor(color_value)
            else:
                # Named color
                return getattr(colors, color_value, colors.black)
        elif isinstance(color_value, list) and len(color_value) >= 3:
            # RGB values
            r, g, b = color_value[:3]
            return colors.Color(r/255, g/255, b/255)
        
        return colors.black
    
    def create_csv_export(self, labels_data: list[dict[str, str]]) -> str:
        """Create CSV export using Polars."""
        try:
            if not labels_data:
                return ""
            
            # Convert to Polars DataFrame
            df = pl.DataFrame(labels_data)
            
            # Return as CSV string
            return df.write_csv()
            
        except Exception as e:
            print(f"Error creating CSV export: {e}")
            return ""
    
    def create_excel_export(self, labels_data: list[dict[str, str]], filename: str = None) -> bytes:
        """Create Excel export using Polars (if xlsxwriter is available)."""
        try:
            if not labels_data:
                return b""
            
            # Convert to Polars DataFrame
            df = pl.DataFrame(labels_data)
            
            # Write to Excel bytes
            buffer = BytesIO()
            df.write_excel(buffer)
            return buffer.getvalue()
            
        except Exception as e:
            print(f"Error creating Excel export: {e}")
            return b""
    
    def create_template_from_label(self, label_data: dict[str, str], template_name: str) -> bool:
        """Create a reusable template from label data."""
        try:
            template_data = {
                'name': template_name,
                'created': datetime.now().isoformat(),
                'fields': label_data,
                'field_count': len(label_data)
            }
            
            return self.storage.save_template(template_name, template_data)
            
        except Exception as e:
            print(f"Error creating template: {e}")
            return False
    
    def get_export_statistics(self, labels_data: list[dict[str, str]]) -> dict[str, any]:
        """Get statistics about the export data using Polars analysis."""
        if not labels_data:
            return {}
        
        try:
            df = pl.DataFrame(labels_data)
            
            stats = {
                'total_labels': len(labels_data),
                'total_fields': len(df.columns),
                'field_names': df.columns,
                'completion_stats': {}
            }
            
            # Calculate completion percentage for each field
            for column in df.columns:
                non_empty = df.filter(pl.col(column).str.strip_chars() != "").height
                completion_percentage = (non_empty / len(labels_data)) * 100
                stats['completion_stats'][column] = {
                    'filled': non_empty,
                    'empty': len(labels_data) - non_empty,
                    'percentage': round(completion_percentage, 1)
                }
            
            return stats
            
        except Exception as e:
            print(f"Error calculating export statistics: {e}")
            return {}
    
    def optimize_multi_label_layout(self, labels_data: list[dict[str, str]], 
                                   template_name: str = "Standard") -> dict[str, any]:
        """Optimize layout for multi-label sheets based on content analysis."""
        template = self.label_templates.get(template_name, self.label_templates['Standard'])
        
        if not labels_data:
            return template
        
        try:
            # Analyze content to optimize layout
            df = pl.DataFrame(labels_data)
            
            # Calculate average content length
            total_chars = 0
            total_fields = 0
            
            for column in df.columns:
                char_counts = df.select(pl.col(column).str.len_chars().sum()).item()
                total_chars += char_counts
                total_fields += df.height
            
            avg_chars_per_field = total_chars / total_fields if total_fields > 0 else 0
            avg_fields_per_label = len(df.columns)
            
            # Adjust font size based on content density
            optimized_template = template.copy()
            
            if avg_chars_per_field > 50 or avg_fields_per_label > 8:
                # Reduce font size for content-heavy labels
                optimized_template['suggested_font_size'] = max(8, template.get('font_size', 10) - 2)
            elif avg_chars_per_field < 20 and avg_fields_per_label < 4:
                # Increase font size for simple labels
                optimized_template['suggested_font_size'] = min(14, template.get('font_size', 10) + 2)
            
            optimized_template['content_analysis'] = {
                'avg_chars_per_field': avg_chars_per_field,
                'avg_fields_per_label': avg_fields_per_label,
                'total_labels': len(labels_data),
                'estimated_pages': max(1, len(labels_data) // (template['labels_per_row'] * template['labels_per_col']))
            }
            
            return optimized_template
            
        except Exception as e:
            print(f"Error optimizing layout: {e}")
            return template
    
    def batch_export_labels(self, labels_data: list[dict[str, str]], 
                           export_formats: list[str], style_data: str = None,
                           template_name: str = "Standard") -> dict[str, bytes]:
        """Batch export labels in multiple formats."""
        results = {}
        
        for format_name in export_formats:
            try:
                if format_name.lower() == 'pdf':
                    if len(labels_data) == 1:
                        results['pdf'] = self.create_single_label_pdf(
                            labels_data[0], style_data, template_name
                        )
                    else:
                        results['pdf'] = self.create_multi_label_sheet(
                            labels_data, style_data, template_name
                        )
                
                elif format_name.lower() == 'csv':
                    results['csv'] = self.create_csv_export(labels_data).encode('utf-8')
                
                elif format_name.lower() == 'excel':
                    results['excel'] = self.create_excel_export(labels_data)
                
            except Exception as e:
                print(f"Error exporting to {format_name}: {e}")
        
        return results


def initialize_export_engine(storage: SimpleStorage) -> ExportEngine:
    """Initialize the export engine."""
    return ExportEngine(storage)