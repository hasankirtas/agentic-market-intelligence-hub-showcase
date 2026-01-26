"""
Change detection utilities for competitive intelligence.
Rule-based diff algorithms and severity scoring.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid
from models.change_detection import ChangeRecord


def detect_price_changes(
    baseline_pricing: Dict[str, Any],
    current_pricing: Dict[str, Any],
    url: str,
    scan_id: str
) -> List[ChangeRecord]:
    """
    Detect price changes between baseline and current pricing data.
    
    Args:
        baseline_pricing: Previous pricing data (e.g., {"pro": {"price": 20}})
        current_pricing: Current pricing data (e.g., {"pro": {"price": 25}})
        url: Source URL
        scan_id: Scan identifier
    
    Returns:
        List of ChangeRecord objects for detected price changes
    """
    changes = []
    
    # Check all tiers in current pricing
    for tier_name, tier_data in current_pricing.items():
        if not isinstance(tier_data, dict):
            continue
        
        current_price = tier_data.get("price")
        if current_price is None:
            continue
        
        # Get baseline price for this tier
        baseline_tier = baseline_pricing.get(tier_name, {})
        baseline_price = baseline_tier.get("price") if isinstance(baseline_tier, dict) else None
        
        # If no baseline, this is a new tier (handled separately)
        if baseline_price is None:
            continue
        
        # Check if price changed
        if current_price != baseline_price:
            # Calculate percentage change
            if baseline_price > 0:
                change_percent = ((current_price - baseline_price) / baseline_price) * 100
            else:
                change_percent = 100.0 if current_price > 0 else 0.0
            
            # Calculate severity
            severity = calculate_price_severity(abs(change_percent))
            
            # Determine if critical (>= 20% change)
            is_critical = abs(change_percent) >= 20.0
            
            change = ChangeRecord(
                change_id=str(uuid.uuid4()),
                scan_id=scan_id,
                url=url,
                change_type="price_change",
                tier_name=tier_name,
                previous_value=baseline_price,
                current_value=current_price,
                change_percent=change_percent,
                severity=severity,
                is_critical=is_critical,
                detected_at=datetime.utcnow()
            )
            changes.append(change)
    
    # Check for removed tiers (price dropped to 0 or tier removed)
    for tier_name, tier_data in baseline_pricing.items():
        if not isinstance(tier_data, dict):
            continue
        
        baseline_price = tier_data.get("price")
        if baseline_price is None or baseline_price == 0:
            continue
        
        # Check if tier still exists
        if tier_name not in current_pricing:
            # Tier was removed
            severity = 0.7  # High severity for tier removal
            change = ChangeRecord(
                change_id=str(uuid.uuid4()),
                scan_id=scan_id,
                url=url,
                change_type="tier_removed",
                tier_name=tier_name,
                previous_value=baseline_price,
                current_value=0,
                change_percent=-100.0,
                severity=severity,
                is_critical=True,
                detected_at=datetime.utcnow()
            )
            changes.append(change)
    
    return changes


def detect_limit_changes(
    baseline_limits: Dict[str, Any],
    current_limits: Dict[str, Any],
    url: str,
    scan_id: str
) -> List[ChangeRecord]:
    """
    Detect limit changes between baseline and current data.
    
    Args:
        baseline_limits: Previous limits data
        current_limits: Current limits data
        url: Source URL
        scan_id: Scan identifier
    
    Returns:
        List of ChangeRecord objects for detected limit changes
    """
    changes = []
    
    # Check all limits in current data
    for limit_key, current_value in current_limits.items():
        baseline_value = baseline_limits.get(limit_key)
        
        # If no baseline, this is a new limit (handled separately)
        if baseline_value is None:
            continue
        
        # Check if limit changed
        if current_value != baseline_value:
            # Try to extract numeric values for percentage calculation
            change_percent = None
            severity = 0.5  # Default medium severity
            
            if isinstance(current_value, (int, float)) and isinstance(baseline_value, (int, float)):
                if baseline_value > 0:
                    change_percent = ((current_value - baseline_value) / baseline_value) * 100
                else:
                    change_percent = 100.0 if current_value > 0 else 0.0
                
                # Calculate severity based on reduction (negative change is more critical)
                if change_percent < 0:
                    severity = calculate_limit_severity(abs(change_percent))
                else:
                    severity = 0.4  # Limit increase is less critical
            
            # Determine if critical (>= 25% reduction)
            is_critical = change_percent is not None and change_percent <= -25.0
            
            change = ChangeRecord(
                change_id=str(uuid.uuid4()),
                scan_id=scan_id,
                url=url,
                change_type="limit_change",
                tier_name=None,
                previous_value=baseline_value,
                current_value=current_value,
                change_percent=change_percent,
                severity=severity,
                is_critical=is_critical,
                detected_at=datetime.utcnow(),
                metadata={"limit_key": limit_key}
            )
            changes.append(change)
    
    return changes


def detect_tier_changes(
    baseline_tiers: List[Dict[str, Any]],
    current_tiers: List[Dict[str, Any]],
    url: str,
    scan_id: str
) -> List[ChangeRecord]:
    """
    Detect tier additions and removals.
    
    Args:
        baseline_tiers: Previous tiers list
        current_tiers: Current tiers list
        url: Source URL
        scan_id: Scan identifier
    
    Returns:
        List of ChangeRecord objects for detected tier changes
    """
    changes = []
    
    # Extract tier names
    baseline_tier_names = {tier.get("name", "").lower() for tier in baseline_tiers if tier.get("name")}
    current_tier_names = {tier.get("name", "").lower() for tier in current_tiers if tier.get("name")}
    
    # Detect new tiers
    new_tiers = current_tier_names - baseline_tier_names
    for tier_name in new_tiers:
        # Find tier data
        tier_data = next((t for t in current_tiers if t.get("name", "").lower() == tier_name), None)
        if tier_data:
            severity = 0.6  # Moderate severity for new tier
            change = ChangeRecord(
                change_id=str(uuid.uuid4()),
                scan_id=scan_id,
                url=url,
                change_type="tier_added",
                tier_name=tier_name,
                previous_value=None,
                current_value=tier_data,
                change_percent=None,
                severity=severity,
                is_critical=False,
                detected_at=datetime.utcnow()
            )
            changes.append(change)
    
    # Detect removed tiers (already handled in detect_price_changes, but for completeness)
    removed_tiers = baseline_tier_names - current_tier_names
    for tier_name in removed_tiers:
        tier_data = next((t for t in baseline_tiers if t.get("name", "").lower() == tier_name), None)
        if tier_data:
            severity = 0.7  # High severity for tier removal
            change = ChangeRecord(
                change_id=str(uuid.uuid4()),
                scan_id=scan_id,
                url=url,
                change_type="tier_removed",
                tier_name=tier_name,
                previous_value=tier_data,
                current_value=None,
                change_percent=-100.0,
                severity=severity,
                is_critical=True,
                detected_at=datetime.utcnow()
            )
            changes.append(change)
    
    return changes


def detect_feature_changes(
    baseline_features: List[str],
    current_features: List[str],
    url: str,
    scan_id: str,
    tier_name: Optional[str] = None
) -> List[ChangeRecord]:
    """
    Detect feature additions and removals.
    
    Args:
        baseline_features: Previous features list
        current_features: Current features list
        url: Source URL
        scan_id: Scan identifier
        tier_name: Optional tier name if features are tier-specific
    
    Returns:
        List of ChangeRecord objects for detected feature changes
    """
    changes = []
    
    baseline_set = set(baseline_features)
    current_set = set(current_features)
    
    # Detect added features
    added_features = current_set - baseline_set
    for feature in added_features:
        severity = 0.5  # Moderate severity for feature addition
        change = ChangeRecord(
            change_id=str(uuid.uuid4()),
            scan_id=scan_id,
            url=url,
            change_type="feature_added",
            tier_name=tier_name,
            previous_value=None,
            current_value=feature,
            change_percent=None,
            severity=severity,
            is_critical=False,
            detected_at=datetime.utcnow()
        )
        changes.append(change)
    
    # Detect removed features (more critical)
    removed_features = baseline_set - current_set
    for feature in removed_features:
        severity = 0.7  # High severity for feature removal
        change = ChangeRecord(
            change_id=str(uuid.uuid4()),
            scan_id=scan_id,
            url=url,
            change_type="feature_removed",
            tier_name=tier_name,
            previous_value=feature,
            current_value=None,
            change_percent=-100.0,
            severity=severity,
            is_critical=True,
            detected_at=datetime.utcnow()
        )
        changes.append(change)
    
    return changes


def calculate_price_severity(change_percent: float) -> float:
    """
    Calculate severity score for price changes (rule-based).
    
    Args:
        change_percent: Absolute percentage change
    
    Returns:
        Severity score between 0.0 and 1.0
    """
    if change_percent >= 30.0:
        return 1.0  # Critical
    elif change_percent >= 20.0:
        return 0.9  # Very High
    elif change_percent >= 10.0:
        return 0.7  # High
    elif change_percent >= 5.0:
        return 0.5  # Medium
    else:
        return 0.3  # Low


def calculate_limit_severity(reduction_percent: float) -> float:
    """
    Calculate severity score for limit reductions (rule-based).
    
    Args:
        reduction_percent: Percentage reduction (positive value)
    
    Returns:
        Severity score between 0.0 and 1.0
    """
    if reduction_percent >= 50.0:
        return 0.9  # Critical
    elif reduction_percent >= 25.0:
        return 0.7  # High
    elif reduction_percent >= 10.0:
        return 0.5  # Medium
    else:
        return 0.3  # Low


def generate_insight(change: ChangeRecord, site_name: str) -> str:
    """
    Generate a rule-based insight sentence for a change.
    
    Args:
        change: ChangeRecord object
        site_name: Name of the site (e.g., "Vercel", "Netlify")
    
    Returns:
        Human-readable insight sentence
    """
    tier_display = change.tier_name.title() if change.tier_name else ""
    
    if change.change_type == "price_change":
        if change.change_percent and change.change_percent > 0:
            return (
                f"{site_name} {tier_display} planı "
                f"%{abs(change.change_percent):.1f} zamlandı "
                f"(${change.previous_value} → ${change.current_value})"
            )
        elif change.change_percent and change.change_percent < 0:
            return (
                f"{site_name} {tier_display} planı "
                f"%{abs(change.change_percent):.1f} indirildi "
                f"(${change.previous_value} → ${change.current_value})"
            )
        else:
            return f"{site_name} {tier_display} planı fiyatı değişti"
    
    elif change.change_type == "limit_change":
        limit_key = change.metadata.get("limit_key", "limit") if change.metadata else "limit"
        if change.change_percent and change.change_percent < 0:
            return (
                f"{site_name} {limit_key} limiti "
                f"%{abs(change.change_percent):.1f} azaldı"
            )
        elif change.change_percent and change.change_percent > 0:
            return (
                f"{site_name} {limit_key} limiti "
                f"%{abs(change.change_percent):.1f} artırıldı"
            )
        else:
            return f"{site_name} {limit_key} limiti değişti"
    
    elif change.change_type == "tier_added":
        return f"{site_name} yeni tier ekledi: {tier_display}"
    
    elif change.change_type == "tier_removed":
        return f"{site_name} {tier_display} tier'ını kaldırdı"
    
    elif change.change_type == "feature_added":
        return f"{site_name} {tier_display} planına {change.current_value} özelliği eklendi"
    
    elif change.change_type == "feature_removed":
        return f"{site_name} {tier_display} planından {change.previous_value} özelliği kaldırıldı"
    
    else:
        return f"{site_name} değişiklik tespit edildi: {change.change_type}"


def extract_site_name(url: str) -> str:
    """
    Extract site name from URL.
    
    Args:
        url: Source URL
    
    Returns:
        Site name (e.g., "Vercel", "Netlify")
    """
    from urllib.parse import urlparse
    
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    # Remove www. prefix
    domain = domain.replace("www.", "")
    
    # Extract site name
    if "vercel" in domain:
        return "Vercel"
    elif "netlify" in domain:
        return "Netlify"
    elif "cloudflare" in domain:
        return "Cloudflare Pages"
    else:
        # Fallback: use domain name
        return domain.split(".")[0].title()

