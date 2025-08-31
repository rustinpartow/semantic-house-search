#!/usr/bin/env python3
"""
Aggressive Property Filter - Remove properties with parking/remodeling issues
"""

import json
from datetime import datetime

def aggressive_filter():
    """Remove properties with clear parking or remodeling issues"""
    
    # Load the already filtered data
    with open('market_scan_multi_data_filtered.json', 'r') as f:
        data = json.load(f)
    
    properties = data['properties']
    removed_properties = []
    
    print(f"Starting with {len(properties)} properties...")
    
    # Properties to remove based on your criteria
    properties_to_remove = []
    
    for i, prop in enumerate(properties):
        should_remove = False
        reasons = []
        
        # Remove apartment units with uncertain parking
        if 'APT' in prop['address'] or 'UNIT' in prop['address']:
            should_remove = True
            reasons.append("Apartment unit - parking uncertain")
        
        # Remove properties with only 1 bathroom (likely need renovation)
        elif prop['baths'] == 1:
            should_remove = True
            reasons.append("Only 1 bathroom - needs renovation")
        
        # Remove properties with very low $/sqft (likely fixer-uppers)
        elif prop['price_per_sqft'] < 900:
            should_remove = True
            reasons.append(f"Very low $/sqft (${prop['price_per_sqft']}) - needs work")
        
        # Remove properties with small lots (parking issues)
        elif prop.get('lot_size') and prop['lot_size'] < 1000:
            should_remove = True
            reasons.append(f"Small lot ({prop['lot_size']} sqft) - parking issues")
        
        if should_remove:
            properties_to_remove.append({
                'index': i,
                'property': prop,
                'reasons': reasons,
                'summary': f"{prop['address']} - ${prop['price']:,} ({prop['beds']}bed/{prop['baths']}bath, {prop['sqft']} sqft, {prop['home_type']}, ${prop['price_per_sqft']}/sqft)"
            })
    
    # Show what will be removed
    print(f"\n🚫 REMOVING {len(properties_to_remove)} PROPERTIES:")
    for item in properties_to_remove:
        print(f"  - {item['summary']}")
        print(f"    Reason: {', '.join(item['reasons'])}")
    
    # Remove properties (in reverse order to maintain indices)
    for item in reversed(properties_to_remove):
        removed_prop = properties.pop(item['index'])
        removed_properties.append({
            'property': removed_prop,
            'removal_reason': ', '.join(item['reasons'])
        })
    
    # Update data
    data['properties'] = properties
    data['scan_date'] = datetime.now().isoformat()
    
    # Save aggressively filtered data
    with open('market_scan_multi_data_curated.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    # Save removal log
    removal_log = {
        'original_count': len(properties) + len(removed_properties),
        'curated_count': len(properties),
        'removed_count': len(removed_properties),
        'removed_properties': removed_properties,
        'filter_date': datetime.now().isoformat()
    }
    
    with open('market_scan_multi_data_curated_removal_log.json', 'w') as f:
        json.dump(removal_log, f, indent=2)
    
    print(f"\n✅ FINAL RESULTS:")
    print(f"   Original: 41 properties")
    print(f"   Auto-filtered: 38 properties")
    print(f"   Curated: {len(properties)} properties")
    print(f"   Total removed: {41 - len(properties)} properties")
    
    print(f"\n📁 Files created:")
    print(f"   - market_scan_multi_data_curated.json")
    print(f"   - market_scan_multi_data_curated_removal_log.json")
    
    return len(properties)

if __name__ == '__main__':
    aggressive_filter() 