"""
Data export module for business leads.

Handles exporting to CSV, JSON, and SQLite formats with email support.
"""

import json
from datetime import datetime
import csv
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict
import pandas as pd


class DataExporter:
    """Export business leads to multiple formats."""
    
    def __init__(self, config, output_dir='./data'):
        """
        Initialize the data exporter.
        
        Args:
            config: Configuration object
            output_dir: Directory for output files
        """
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def export(self, data: List[Dict], formats: List[str], filename: str) -> List[str]:
        """
        Export data to specified formats.
        
        Args:
            data: List of business dictionaries
            formats: List of format strings ('csv', 'json', 'sqlite')
            filename: Base filename (without extension)
            
        Returns:
            List of created file paths
        """
        exported_files = []
        
        for fmt in formats:
            if fmt == 'csv':
                file_path = self._export_csv(data, filename)
            elif fmt == 'json':
                file_path = self._export_json(data, filename)
            elif fmt == 'sqlite':
                file_path = self._export_sqlite(data, filename)
            elif fmt == 'excel':
                file_path = self._export_excel(data, filename)
            else:
                self.logger.warning(f"Unknown format: {fmt}")
                continue
            
            if file_path:
                exported_files.append(file_path)
                self.logger.info(f"✓ Exported to {fmt.upper()}: {file_path}")
        
        return exported_files
    
    def _export_csv(self, data: List[Dict], filename: str) -> str:
        """Export to CSV format with email field."""
        file_path = self.output_dir / f"{filename}.csv"
        
        if not data:
            self.logger.warning("No data to export to CSV")
            return str(file_path)
        
        # Define column order - EMAIL ADDED

        columns = [
            'place_id', 'name', 'address', 'phone', 'email', 'website',
            'opening_hours', 'price_level',
            'facebook', 'instagram', 'twitter', 'linkedin', 'youtube', 'tiktok', 'whatsapp_status',
            'category', 'rating', 'reviews', 'latitude', 'longitude',
            'maps_url', 'source_url', 'timestamp', 'labels'
        ]
        
        # Write CSV
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data)
        
        return str(file_path)
    
    def _export_json(self, data: List[Dict], filename: str) -> str:
        """Export to JSON format."""
        file_path = self.output_dir / f"{filename}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return str(file_path)
    
    def _export_sqlite(self, data: List[Dict], filename: str) -> str:
        """Export to SQLite database with proper schema including email."""
        file_path = self.output_dir / f"{filename}.db"
        
        if not data:
            self.logger.warning("No data to export to SQLite")
            return str(file_path)
        
        # Connect to SQLite
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        
        # Get table name from config
        table_name = self.config.export.get('sqlite_table_name', 'leads')
        
        # Create table with EMAIL field
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                place_id TEXT,
                name TEXT NOT NULL,
                address TEXT,
                phone TEXT,
                email TEXT,

                website TEXT,
                facebook TEXT,
                instagram TEXT,
                twitter TEXT,
                linkedin TEXT,
                youtube TEXT,
                tiktok TEXT,
                whatsapp_status TEXT,
                opening_hours TEXT,
                price_level TEXT,
                category TEXT,
                rating REAL,
                reviews INTEGER,
                latitude REAL,
                longitude REAL,
                maps_url TEXT,
                source_url TEXT,
                timestamp TEXT,
                labels TEXT,
                PRIMARY KEY (place_id)
            )
        ''')
        
        # Insert data with EMAIL field
        inserted_count = 0
        for row in data:
            try:
                cursor.execute(f'''
                    INSERT OR REPLACE INTO {table_name} 
                    (place_id, name, address, phone, email, website, 
                     facebook, instagram, twitter, linkedin, youtube, tiktok, whatsapp_status,
                     opening_hours, price_level,
                     category, rating, reviews, latitude, longitude, maps_url, 
                     source_url, timestamp, labels)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('place_id'),
                    row.get('name'),
                    row.get('address'),
                    row.get('phone'),
                    row.get('email'),  # EMAIL FIELD ADDED

                    row.get('website'),
                    row.get('facebook'),
                    row.get('instagram'),
                    row.get('twitter'),
                    row.get('linkedin'),
                    row.get('youtube'),
                    row.get('tiktok'),
                    row.get('whatsapp_status'),
                    row.get('opening_hours'),
                    row.get('price_level'),
                    row.get('category'),
                    row.get('rating'),
                    row.get('reviews'),
                    row.get('latitude'),
                    row.get('longitude'),
                    row.get('maps_url'),
                    row.get('source_url'),
                    row.get('timestamp'),
                    row.get('labels')
                ))
                inserted_count += 1
            except sqlite3.Error as e:
                self.logger.warning(f"Error inserting row: {e}")
                continue
        
        # Commit and close
        conn.commit()
        
        # Log statistics
        cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
        count = cursor.fetchone()[0]
        self.logger.info(f"SQLite: Inserted {inserted_count} records into {table_name} (total: {count})")
        
        conn.close()
        
        return str(file_path)

    def _export_excel(self, data: List[Dict], filename: str) -> str:
        """Export to beautifully formatted Excel file with advanced features."""
        file_path = self.output_dir / f"{filename}.xlsx"
        
        if not data:
            self.logger.warning("No data to export to Excel")
            return str(file_path)

        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Define column order - Organized by function
        # 1. Contact Info
        contact_cols = ['name', 'category', 'phone', 'email', 'website', 'address', 'opening_hours', 'price_level']
        # 2. Social Media
        social_cols = ['facebook', 'instagram', 'twitter', 'linkedin', 'youtube', 'tiktok', 'whatsapp_status']
        # 3. Metrics
        metric_cols = ['rating', 'reviews']
        # 4. Meta
        meta_cols = ['status', 'next_action', 'notes', 'maps_url', 'place_id'] # Lowercase for matching logic, will title case later
        
        # Prepare DataFrame columns
        final_cols = []
        for col in contact_cols + social_cols + metric_cols:
            if col in df.columns:
                final_cols.append(col)
            elif col in social_cols: # Add missing social cols
                df[col] = ''
                final_cols.append(col)
        
        # Add CRM columns if not present
        if 'Status' not in df.columns: df['Status'] = 'New'
        if 'Next Action' not in df.columns: df['Next Action'] = ''
        if 'Notes' not in df.columns: df['Notes'] = ''
        
        crm_cols = ['Status', 'Next Action', 'Notes']
        
        # Add remaining existing columns not in our specific lists
        existing_others = [c for c in df.columns if c not in final_cols and c not in crm_cols and c not in ['status', 'next_action', 'notes']]
        
        # Final Column Order
        ordered_cols = final_cols + crm_cols + existing_others
        # Filter to only columns that actually exist now
        ordered_cols = [c for c in ordered_cols if c in df.columns]
        
        df = df[ordered_cols]
        
        # Rename columns for professional look
        col_mapping = {
            'name': 'Business Name',
            'category': 'Category',
            'phone': 'Phone Number',
            'website': 'Website',
            'address': 'Full Address',
            'opening_hours': 'Opening Hours',
            'price_level': 'Price Level',
            'rating': 'Rating',
            'reviews': 'Review Count',
            'facebook': 'Facebook',
            'instagram': 'Instagram',
            'twitter': 'X / Twitter',
            'linkedin': 'LinkedIn',
            'youtube': 'YouTube',
            'tiktok': 'TikTok',
            'whatsapp_status': 'WhatsApp Availability',
            'maps_url': 'Google Maps Link',
            'place_id': 'Place ID'
        }
        df.rename(columns=col_mapping, inplace=True)

        # Create Excel writer
        writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Leads', index=False, startrow=1, header=False)

        workbook = writer.book
        worksheet = writer.sheets['Leads']

        # --- Formats ---
        
        # Headers
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'center',
            'fg_color': '#2C3E50',
            'font_color': 'white',
            'border': 1,
            'font_size': 11
        })
        
        metric_header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'center',
            'fg_color': '#27ae60', # Green for metrics
            'font_color': 'white',
            'border': 1,
            'font_size': 11
        })
        
        crm_header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'center',
            'fg_color': '#e67e22', # Orange for CRM
            'font_color': 'white',
            'border': 1,
            'font_size': 11
        })
        
        # Data Formats
        text_wrap = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1, 'border_color': '#E0E0E0'})
        
        # Write Title
        title_format = workbook.add_format({
            'bold': True, 'font_size': 16, 'font_color': '#2C3E50'
        })
        worksheet.write(0, 0, f"Business Leads Export - {datetime.now().strftime('%Y-%m-%d')}", title_format)

        # Write Headers with proper formatting
        for col_num, value in enumerate(df.columns.values):
            fmt = header_format
            if value in ['Rating', 'Review Count']:
                fmt = metric_header_format
            elif value in ['Status', 'Next Action', 'Notes']:
                fmt = crm_header_format
            elif value in ['Facebook', 'Instagram', 'X / Twitter', 'LinkedIn', 'YouTube', 'TikTok']:
                fmt = workbook.add_format({'bold': True, 'align': 'center', 'fg_color': '#3498db', 'font_color': 'white', 'border': 1})
            elif value == 'WhatsApp Availability':
                fmt = workbook.add_format({'bold': True, 'align': 'center', 'fg_color': '#25D366', 'font_color': 'white', 'border': 1})
                
            worksheet.write(1, col_num, value, fmt)

        # Set Column Widths and Formatting
        worksheet.set_column('A:A', 35, text_wrap) # Name
        worksheet.set_column('B:B', 20, text_wrap) # Category
        worksheet.set_column('C:C', 18, text_wrap) # Phone
        worksheet.set_column('D:D', 30, text_wrap) # Email
        worksheet.set_column('E:E', 30, text_wrap) # Website
        worksheet.set_column('F:F', 40, text_wrap) # Address
        
        # Social Media Columns (G-L roughly) - set simpler width
        # Dynamic finding of column indices would be better, but we know the order roughly.
        # Let's iterate to be safe.
        for idx, col_name in enumerate(df.columns):
            if col_name in ['Facebook', 'Instagram', 'X / Twitter', 'LinkedIn', 'YouTube', 'TikTok']:
                worksheet.set_column(idx, idx, 25, text_wrap)
            elif col_name == 'WhatsApp Availability':
                worksheet.set_column(idx, idx, 22, self._get_center_format(workbook))
            elif col_name == 'Rating':
                worksheet.set_column(idx, idx, 10, self._get_center_format(workbook))
            elif col_name == 'Review Count':
                worksheet.set_column(idx, idx, 12, self._get_center_format(workbook))
            elif col_name == 'Status':
                worksheet.set_column(idx, idx, 15, workbook.add_format({'bg_color': '#FFF9C4', 'border': 1}))
                # Add validation
                worksheet.data_validation(2, idx, len(df)+1, idx, {
                    'validate': 'list',
                    'source': ['New', 'Contacted', 'Qualified', 'Lost', 'Closed'],
                })

        # Add AutoFilter
        worksheet.autofilter(1, 0, len(df)+1, len(df.columns)-1)
        
        # Freeze Panes (Top 2 rows)
        worksheet.freeze_panes(2, 0)
        
        # Conditional Formatting for Rating (Data Bar)
        if 'Rating' in df.columns:
            try:
                rating_idx = df.columns.get_loc('Rating')
                worksheet.conditional_format(2, rating_idx, len(df)+1, rating_idx, {
                    'type': 'data_bar',
                    'bar_color': '#63C384',
                    'bar_solid': True,
                    'min_type': 'num', 'min_value': 0,
                    'max_type': 'num', 'max_value': 5
                })
            except:
                pass

        writer.close()
        return str(file_path)
    
    def _get_center_format(self, workbook):
        return workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1, 'border_color': '#E0E0E0'})
