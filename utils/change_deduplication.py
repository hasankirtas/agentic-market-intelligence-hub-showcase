"""
Change deduplication utilities.

Provides functions to deduplicate change records based on various strategies.
"""
from typing import List, Dict, Any
from collections import defaultdict


def deduplicate_changes(changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate change records, keeping the most severe change per URL and type.
    
    When the same change is detected in multiple scans (e.g., price change detected
    at 10:00 and again at 11:00), we keep only the highest severity instance to
    avoid duplicate reporting.
    
    Strategy:
    - Group by (url, change_type)
    - For each group, keep the change with highest severity
    - Preserve all other attributes from the highest severity change
    
    Args:
        changes: List of change records
    
    Returns:
        Deduplicated list of changes
    
    Example:
        Input:
        [
            {"url": "vercel.com", "change_type": "price_change", "severity": 0.6},
            {"url": "vercel.com", "change_type": "price_change", "severity": 0.8},
            {"url": "netlify.com", "change_type": "limit_change", "severity": 0.5}
        ]
        
        Output:
        [
            {"url": "vercel.com", "change_type": "price_change", "severity": 0.8},
            {"url": "netlify.com", "change_type": "limit_change", "severity": 0.5}
        ]
    """
    if not changes:
        return []
    
    # Group changes by (url, change_type)
    grouped = defaultdict(list)
    for change in changes:
        url = change.get("url", "")
        change_type = change.get("change_type", "")
        key = (url, change_type)
        grouped[key].append(change)
    
    # For each group, keep the change with highest severity
    deduplicated = []
    for key, group in grouped.items():
        # Find change with max severity
        max_change = max(group, key=lambda c: c.get("severity", 0.0))
        deduplicated.append(max_change)
    
    # Sort by severity (descending) for consistent ordering
    deduplicated.sort(key=lambda c: c.get("severity", 0.0), reverse=True)
    
    return deduplicated


def deduplicate_by_description(changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate changes based on description similarity.
    
    More aggressive deduplication that considers the description text.
    Useful when the same change might be reported with slightly different attributes.
    
    Args:
        changes: List of change records
    
    Returns:
        Deduplicated list of changes
    """
    if not changes:
        return []
    
    seen_descriptions = set()
    deduplicated = []
    
    for change in changes:
        description = change.get("description", "").strip().lower()
        if description and description not in seen_descriptions:
            seen_descriptions.add(description)
            deduplicated.append(change)
    
    # Sort by severity
    deduplicated.sort(key=lambda c: c.get("severity", 0.0), reverse=True)
    
    return deduplicated


def aggregate_change_statistics(changes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate statistics about a list of changes.
    
    Useful for report summaries and logging.
    
    Args:
        changes: List of change records
    
    Returns:
        Statistics dictionary
    """
    if not changes:
        return {
            "total_count": 0,
            "by_type": {},
            "by_severity_level": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "average_severity": 0.0,
            "max_severity": 0.0
        }
    
    # Count by type
    by_type = defaultdict(int)
    for change in changes:
        change_type = change.get("change_type", "unknown")
        by_type[change_type] += 1
    
    # Count by severity level
    by_severity_level = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    severities = []
    
    for change in changes:
        severity = change.get("severity", 0.0)
        severities.append(severity)
        
        if severity >= 0.9:
            by_severity_level["critical"] += 1
        elif severity >= 0.7:
            by_severity_level["high"] += 1
        elif severity >= 0.5:
            by_severity_level["medium"] += 1
        else:
            by_severity_level["low"] += 1
    
    return {
        "total_count": len(changes),
        "by_type": dict(by_type),
        "by_severity_level": by_severity_level,
        "average_severity": sum(severities) / len(severities) if severities else 0.0,
        "max_severity": max(severities) if severities else 0.0
    }

