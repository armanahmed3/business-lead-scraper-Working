"""
Enhanced Lead Database Module
Handles lead storage, deduplication, and data management
"""

import sqlite3
import pandas as pd
import hashlib
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LeadRecord:
    """Lead record structure for database operations"""
    id: Optional[int] = None
    name: str = ""
    address: str = ""
    city: str = ""
    country: str = ""
    niche: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    source: str = ""
    scraped_at: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class LeadDatabase:
    """Enhanced database manager for lead storage and deduplication"""
    
    def __init__(self, db_path: str = "leadai_pro.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database with enhanced schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create leads table with enhanced schema
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS leads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        address TEXT NOT NULL,
                        city TEXT NOT NULL,
                        country TEXT NOT NULL,
                        niche TEXT NOT NULL,
                        phone TEXT DEFAULT '',
                        email TEXT DEFAULT '',
                        website TEXT DEFAULT '',
                        source TEXT NOT NULL,
                        scraped_at TEXT DEFAULT '',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        name_hash TEXT,
                        address_hash TEXT,
                        email_hash TEXT,
                        phone_hash TEXT
                    )
                """)
                
                # Add unique constraints after table creation
                try:
                    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_name_address ON leads(name_hash, address_hash)")
                    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_email_phone ON leads(email_hash, phone_hash)")
                except sqlite3.OperationalError as e:
                    logger.warning(f"Could not create unique constraints: {e}")
                
                # Create deduplication log table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS deduplication_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        operation_type TEXT NOT NULL,
                        total_leads INTEGER,
                        duplicates_found INTEGER,
                        duplicates_removed INTEGER,
                        final_count INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                
                # Create indexes for better performance (after table creation)
                try:
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_name_hash ON leads(name_hash)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_address_hash ON leads(address_hash)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_hash ON leads(email_hash)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_phone_hash ON leads(phone_hash)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_source ON leads(source)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_city_country ON leads(city, country)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_niche ON leads(niche)")
                    conn.commit()
                except sqlite3.OperationalError as e:
                    # If indexes fail, continue without them
                    logger.warning(f"Could not create some indexes: {e}")
                
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _generate_hash(self, text: str) -> str:
        """Generate hash for text (used for deduplication)"""
        if not text:
            return ""
        return hashlib.md5(text.lower().strip().encode()).hexdigest()
    
    def _prepare_lead_data(self, lead_data: Dict) -> LeadRecord:
        """Prepare lead data for database insertion"""
        return LeadRecord(
            name=lead_data.get('name', ''),
            address=lead_data.get('address', ''),
            city=lead_data.get('city', ''),
            country=lead_data.get('country', ''),
            niche=lead_data.get('niche', ''),
            phone=lead_data.get('phone', ''),
            email=lead_data.get('email', ''),
            website=lead_data.get('website', ''),
            source=lead_data.get('source', ''),
            scraped_at=lead_data.get('scraped_at', ''),
            created_at=datetime.now().isoformat()
        )
    
    def insert_leads(self, leads_data: List[Dict]) -> Tuple[int, int, int]:
        """
        Insert leads with deduplication
        
        Args:
            leads_data: List of lead dictionaries
            
        Returns:
            Tuple of (total_processed, duplicates_found, successfully_inserted)
        """
        if not leads_data:
            return 0, 0, 0
        
        total_processed = len(leads_data)
        duplicates_found = 0
        successfully_inserted = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for lead_data in leads_data:
                    try:
                        # Prepare lead data
                        lead = self._prepare_lead_data(lead_data)
                        
                        # Generate hashes for deduplication
                        name_hash = self._generate_hash(lead.name)
                        address_hash = self._generate_hash(lead.address)
                        email_hash = self._generate_hash(lead.email)
                        phone_hash = self._generate_hash(lead.phone)
                        
                        # Check for duplicates
                        is_duplicate = self._check_duplicate(
                            cursor, name_hash, address_hash, email_hash, phone_hash
                        )
                        
                        if is_duplicate:
                            duplicates_found += 1
                            continue
                        
                        # Insert new lead
                        cursor.execute("""
                            INSERT INTO leads (
                                name, address, city, country, niche, phone, email, website, 
                                source, scraped_at, created_at, updated_at,
                                name_hash, address_hash, email_hash, phone_hash
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            lead.name, lead.address, lead.city, lead.country, lead.niche,
                            lead.phone, lead.email, lead.website, lead.source, lead.scraped_at,
                            lead.created_at, lead.created_at,
                            name_hash, address_hash, email_hash, phone_hash
                        ))
                        
                        successfully_inserted += 1
                        
                    except sqlite3.IntegrityError:
                        # Handle unique constraint violations
                        duplicates_found += 1
                        continue
                    except Exception as e:
                        logger.warning(f"Error inserting lead {lead_data.get('name', 'Unknown')}: {e}")
                        continue
                
                # Log deduplication operation
                cursor.execute("""
                    INSERT INTO deduplication_log (
                        operation_type, total_leads, duplicates_found, 
                        duplicates_removed, final_count
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    'insert_with_dedup', total_processed, duplicates_found,
                    duplicates_found, successfully_inserted
                ))
                
                conn.commit()
                logger.info(f"Inserted {successfully_inserted} leads, found {duplicates_found} duplicates")
                
        except Exception as e:
            logger.error(f"Error inserting leads: {e}")
            raise
        
        return total_processed, duplicates_found, successfully_inserted
    
    def _check_duplicate(self, cursor, name_hash: str, address_hash: str, 
                        email_hash: str, phone_hash: str) -> bool:
        """Check if lead is duplicate based on multiple criteria"""
        try:
            # Check by name + address
            cursor.execute("""
                SELECT id FROM leads 
                WHERE name_hash = ? AND address_hash = ?
            """, (name_hash, address_hash))
            
            if cursor.fetchone():
                return True
            
            # Check by email + phone (if both exist)
            if email_hash and phone_hash:
                cursor.execute("""
                    SELECT id FROM leads 
                    WHERE email_hash = ? AND phone_hash = ?
                """, (email_hash, phone_hash))
                
                if cursor.fetchone():
                    return True
            
            # Check by email only (if email exists)
            if email_hash:
                cursor.execute("""
                    SELECT id FROM leads 
                    WHERE email_hash = ?
                """, (email_hash,))
                
                if cursor.fetchone():
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking duplicate: {e}")
            return False
    
    def get_leads(self, filters: Optional[Dict] = None, limit: Optional[int] = None) -> List[Dict]:
        """
        Retrieve leads with optional filtering
        
        Args:
            filters: Dictionary of filters (city, country, niche, source)
            limit: Maximum number of leads to return
            
        Returns:
            List of lead dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build query
                query = "SELECT * FROM leads WHERE 1=1"
                params = []
                
                if filters:
                    if filters.get('city'):
                        query += " AND city LIKE ?"
                        params.append(f"%{filters['city']}%")
                    
                    if filters.get('country'):
                        query += " AND country LIKE ?"
                        params.append(f"%{filters['country']}%")
                    
                    if filters.get('niche'):
                        query += " AND niche LIKE ?"
                        params.append(f"%{filters['niche']}%")
                    
                    if filters.get('source'):
                        query += " AND source = ?"
                        params.append(filters['source'])
                
                query += " ORDER BY created_at DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor.execute(query, params)
                columns = [description[0] for description in cursor.description]
                results = cursor.fetchall()
                
                # Convert to list of dictionaries
                leads = []
                for row in results:
                    lead_dict = dict(zip(columns, row))
                    leads.append(lead_dict)
                
                return leads
                
        except Exception as e:
            logger.error(f"Error retrieving leads: {e}")
            return []
    
    def get_lead_stats(self) -> Dict:
        """Get lead statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total leads
                cursor.execute("SELECT COUNT(*) FROM leads")
                total_leads = cursor.fetchone()[0]
                
                # Leads by source
                cursor.execute("""
                    SELECT source, COUNT(*) as count 
                    FROM leads 
                    GROUP BY source 
                    ORDER BY count DESC
                """)
                leads_by_source = dict(cursor.fetchall())
                
                # Leads by city
                cursor.execute("""
                    SELECT city, COUNT(*) as count 
                    FROM leads 
                    GROUP BY city 
                    ORDER BY count DESC 
                    LIMIT 10
                """)
                leads_by_city = dict(cursor.fetchall())
                
                # Leads by niche
                cursor.execute("""
                    SELECT niche, COUNT(*) as count 
                    FROM leads 
                    GROUP BY niche 
                    ORDER BY count DESC 
                    LIMIT 10
                """)
                leads_by_niche = dict(cursor.fetchall())
                
                # Recent activity
                cursor.execute("""
                    SELECT COUNT(*) FROM leads 
                    WHERE created_at >= datetime('now', '-7 days')
                """)
                recent_leads = cursor.fetchone()[0]
                
                return {
                    'total_leads': total_leads,
                    'leads_by_source': leads_by_source,
                    'leads_by_city': leads_by_city,
                    'leads_by_niche': leads_by_niche,
                    'recent_leads': recent_leads
                }
                
        except Exception as e:
            logger.error(f"Error getting lead stats: {e}")
            return {}
    
    def export_to_csv(self, filters: Optional[Dict] = None, filename: Optional[str] = None) -> str:
        """
        Export leads to CSV file
        
        Args:
            filters: Optional filters for lead selection
            filename: Optional custom filename
            
        Returns:
            Path to exported CSV file
        """
        try:
            leads = self.get_leads(filters)
            
            if not leads:
                raise ValueError("No leads found to export")
            
            # Create DataFrame
            df = pd.DataFrame(leads)
            
            # Select relevant columns for export
            export_columns = [
                'name', 'address', 'city', 'country', 'niche', 
                'phone', 'email', 'website', 'source', 'scraped_at'
            ]
            
            # Filter columns that exist
            available_columns = [col for col in export_columns if col in df.columns]
            df_export = df[available_columns]
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"leads_export_{timestamp}.csv"
            
            # Export to CSV
            df_export.to_csv(filename, index=False, encoding='utf-8')
            
            logger.info(f"Exported {len(df_export)} leads to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error exporting leads to CSV: {e}")
            raise
    
    def cleanup_duplicates(self) -> Tuple[int, int]:
        """
        Clean up existing duplicates in database
        
        Returns:
            Tuple of (duplicates_found, duplicates_removed)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Find duplicates by name + address
                cursor.execute("""
                    SELECT name_hash, address_hash, COUNT(*) as count
                    FROM leads 
                    GROUP BY name_hash, address_hash 
                    HAVING count > 1
                """)
                name_address_duplicates = cursor.fetchall()
                
                # Find duplicates by email + phone
                cursor.execute("""
                    SELECT email_hash, phone_hash, COUNT(*) as count
                    FROM leads 
                    WHERE email_hash != '' AND phone_hash != ''
                    GROUP BY email_hash, phone_hash 
                    HAVING count > 1
                """)
                email_phone_duplicates = cursor.fetchall()
                
                duplicates_found = len(name_address_duplicates) + len(email_phone_duplicates)
                duplicates_removed = 0
                
                # Remove duplicates (keep the oldest record)
                for name_hash, address_hash, count in name_address_duplicates:
                    cursor.execute("""
                        DELETE FROM leads 
                        WHERE name_hash = ? AND address_hash = ? 
                        AND id NOT IN (
                            SELECT MIN(id) FROM leads 
                            WHERE name_hash = ? AND address_hash = ?
                        )
                    """, (name_hash, address_hash, name_hash, address_hash))
                    duplicates_removed += cursor.rowcount
                
                for email_hash, phone_hash, count in email_phone_duplicates:
                    cursor.execute("""
                        DELETE FROM leads 
                        WHERE email_hash = ? AND phone_hash = ? 
                        AND id NOT IN (
                            SELECT MIN(id) FROM leads 
                            WHERE email_hash = ? AND phone_hash = ?
                        )
                    """, (email_hash, phone_hash, email_hash, phone_hash))
                    duplicates_removed += cursor.rowcount
                
                # Log cleanup operation
                cursor.execute("""
                    INSERT INTO deduplication_log (
                        operation_type, total_leads, duplicates_found, 
                        duplicates_removed, final_count
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    'cleanup_duplicates', 0, duplicates_found,
                    duplicates_removed, 0
                ))
                
                conn.commit()
                logger.info(f"Cleaned up {duplicates_removed} duplicates")
                
                return duplicates_found, duplicates_removed
                
        except Exception as e:
            logger.error(f"Error cleaning up duplicates: {e}")
            return 0, 0
