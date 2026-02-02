"""
Deduplication module for business leads.

This module handles identifying and removing duplicate business entries
using multiple strategies: exact matching, place_id matching, and fuzzy matching.
"""

import logging
from typing import List, Dict, Set, Tuple
from difflib import SequenceMatcher


class Deduplicator:
    """
    Deduplicate business leads using multiple strategies.
    
    Strategies:
    1. Exact place_id matching (highest priority)
    2. Fuzzy matching on name + address + phone using difflib
    3. Coordinate-based proximity matching
    """
    
    def __init__(self, config):
        """
        Initialize the deduplicator.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.threshold = config.deduplication['fuzzy_threshold']
        self.prefer_place_id = config.deduplication['prefer_place_id']
    
    def deduplicate(self, leads: List[Dict]) -> List[Dict]:
        """
        Deduplicate a list of business leads.
        
        Args:
            leads: List of business dictionaries
            
        Returns:
            List of unique business dictionaries
        """
        if not leads:
            return []
        
        self.logger.info(f"Deduplicating {len(leads)} leads...")
        
        unique_leads = []
        seen_place_ids: Set[str] = set()
        seen_signatures: Set[str] = set()
        
        for lead in leads:
            # Strategy 1: place_id matching
            if self.prefer_place_id and lead.get('place_id'):
                if lead['place_id'] in seen_place_ids:
                    self.logger.debug(f"Duplicate place_id: {lead.get('name')}")
                    continue
                seen_place_ids.add(lead['place_id'])
                unique_leads.append(lead)
                continue
            
            # Strategy 2: Fuzzy matching
            if self._is_duplicate_fuzzy(lead, unique_leads):
                self.logger.debug(f"Fuzzy duplicate: {lead.get('name')}")
                continue
            
            # Strategy 3: Exact signature matching (fallback)
            signature = self._generate_signature(lead)
            if signature in seen_signatures:
                self.logger.debug(f"Duplicate signature: {lead.get('name')}")
                continue
            
            seen_signatures.add(signature)
            unique_leads.append(lead)
        
        removed_count = len(leads) - len(unique_leads)
        self.logger.info(f"Removed {removed_count} duplicates")
        
        return unique_leads
    
    def _is_duplicate_fuzzy(self, lead: Dict, existing_leads: List[Dict]) -> bool:
        """
        Check if lead is a fuzzy duplicate of any existing lead.
        
        Args:
            lead: Business dictionary to check
            existing_leads: List of existing unique leads
            
        Returns:
            True if duplicate found, False otherwise
        """
        for existing in existing_leads:
            similarity = self._calculate_similarity(lead, existing)
            
            if similarity >= self.threshold:
                return True
        
        return False
    
    def _calculate_similarity(self, lead1: Dict, lead2: Dict) -> float:
        """
        Calculate similarity score between two leads.
        
        Uses weighted fuzzy matching on multiple fields using difflib.
        
        Args:
            lead1: First business dictionary
            lead2: Second business dictionary
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Fields to compare with weights
        comparisons = []
        
        # Name comparison (weight: 0.4)
        name1 = lead1.get('name', '')
        name2 = lead2.get('name', '')
        if name1 and name2:
            name_sim = self._string_similarity(name1.lower(), name2.lower())
            comparisons.append(('name', name_sim, 0.4))
        
        # Address comparison (weight: 0.4)
        addr1 = lead1.get('address', '')
        addr2 = lead2.get('address', '')
        if addr1 and addr2:
            addr_sim = self._string_similarity(addr1.lower(), addr2.lower())
            comparisons.append(('address', addr_sim, 0.4))
        
        # Phone comparison (weight: 0.2)
        phone1 = self._normalize_phone(lead1.get('phone', ''))
        phone2 = self._normalize_phone(lead2.get('phone', ''))
        if phone1 and phone2:
            phone_sim = 1.0 if phone1 == phone2 else 0.0
            comparisons.append(('phone', phone_sim, 0.2))
        
        # Coordinate comparison (weight: 0.3)
        if lead1.get('latitude') and lead2.get('latitude'):
            coord_sim = self._coordinate_similarity(
                (lead1['latitude'], lead1['longitude']),
                (lead2['latitude'], lead2['longitude'])
            )
            comparisons.append(('coords', coord_sim, 0.3))
        
        # Calculate weighted average
        if not comparisons:
            return 0.0
        
        total_weight = sum(weight for _, _, weight in comparisons)
        weighted_sum = sum(score * weight for _, score, weight in comparisons)
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _string_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate string similarity using difflib.SequenceMatcher.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity ratio between 0.0 and 1.0
        """
        return SequenceMatcher(None, str1, str2).ratio()
    
    def _coordinate_similarity(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """
        Calculate similarity based on coordinate proximity.
        
        Args:
            coord1: (latitude, longitude) tuple
            coord2: (latitude, longitude) tuple
            
        Returns:
            Similarity score (1.0 if very close, decreasing with distance)
        """
        # Calculate approximate distance in meters
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # Simple Euclidean distance (good enough for small distances)
        # 1 degree ≈ 111km at equator
        distance = ((lat1 - lat2)**2 + (lon1 - lon2)**2)**0.5 * 111000
        
        # Consider matches within 100m as very similar
        if distance < 100:
            return 1.0
        elif distance < 500:
            return 0.8
        elif distance < 1000:
            return 0.5
        else:
            return 0.0
    
    def _normalize_phone(self, phone: str) -> str:
        """
        Normalize phone number for comparison.
        
        Args:
            phone: Phone number string
            
        Returns:
            Normalized phone number (digits only)
        """
        if not phone:
            return ''
        
        # Remove all non-digit characters
        return ''.join(filter(str.isdigit, phone))
    
    def _generate_signature(self, lead: Dict) -> str:
        """
        Generate a deterministic signature for a lead.
        
        Args:
            lead: Business dictionary
            
        Returns:
            Signature string
        """
        # Combine normalized fields
        name = lead.get('name', '').lower().strip()
        address = lead.get('address', '').lower().strip()
        phone = self._normalize_phone(lead.get('phone', ''))
        
        return f"{name}|{address}|{phone}"
