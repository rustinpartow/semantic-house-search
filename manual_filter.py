#!/usr/bin/env python3
"""
Manual Property Filter

This tool helps manually filter properties based on parking availability
and remodeling needs. It loads the current data and provides an interface
to mark properties for removal.
"""

import json
import sys
from datetime import datetime

class PropertyFilter:
    def __init__(self, data_file):
        """Initialize the filter with property data"""
        self.data_file = data_file
        self.data = self.load_data()
        self.properties = self.data['properties']
        self.removed_properties = []
        
    def load_data(self):
        """Load property data from JSON file"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Could not find {self.data_file}")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {self.data_file}")
            sys.exit(1)
    
    def get_property_summary(self, prop):
        """Get a summary string for a property"""
        return (f"{prop['address']} - ${prop['price']:,} "
                f"({prop['beds']}bed/{prop['baths']}bath, {prop['sqft']} sqft, "
                f"{prop['home_type']}, ${prop['price_per_sqft']}/sqft)")
    
    def identify_problematic_properties(self):
        """Identify properties likely to have parking or remodeling issues"""
        problematic = []
        
        for prop in self.properties:
            issues = []
            
            # Check for potential parking issues
            if prop['home_type'] == 'CONDO':
                # Condos in older buildings may lack parking
                if 'APT' in prop['address'] or 'UNIT' in prop['address']:
                    issues.append("Apartment unit - parking uncertain")
            
            # Check for potential remodeling needs
            if prop.get('year_built'):
                try:
                    year = int(prop['year_built'])
                    if year < 1950:
                        issues.append(f"Very old property ({year}) - likely needs updates")
                    elif year < 1980:
                        issues.append(f"Older property ({year}) - may need updates")
                except (ValueError, TypeError):
                    pass
            
            # Check price per sqft anomalies (very low might indicate fixer-upper)
            if prop['price_per_sqft'] < 900:
                issues.append(f"Low $/sqft (${prop['price_per_sqft']}) - may need work")
            
            # Check for very small lot sizes (parking issues)
            lot_size = prop.get('lot_size')
            if lot_size is not None and lot_size < 1000:
                issues.append(f"Small lot ({lot_size} sqft) - parking issues")
            
            # Check for 1 bathroom (may need updates)
            if prop['baths'] == 1:
                issues.append("Only 1 bathroom - may need renovation")
            
            if issues:
                problematic.append({
                    'property': prop,
                    'issues': issues,
                    'summary': self.get_property_summary(prop)
                })
        
        return problematic
    
    def manual_removal_candidates(self):
        """Properties that are likely candidates for manual removal"""
        candidates = []
        
        for prop in self.properties:
            # High-risk properties for removal
            remove_reasons = []
            
            # Turk Street area (can be rough)
            if 'Turk St' in prop['address']:
                remove_reasons.append("Turk Street location")
            
            # Very small apartments
            if prop['home_type'] == 'CONDO' and prop['sqft'] < 1100:
                if 'APT' in prop['address'] or 'UNIT' in prop['address']:
                    remove_reasons.append("Small apartment unit")
            
            # Properties with concerning characteristics
            if prop['price_per_sqft'] < 950 and prop['baths'] == 1:
                remove_reasons.append("Low $/sqft + minimal bathrooms")
            
            # Properties with zero or tiny lot sizes
            lot_size = prop.get('lot_size')
            if lot_size is not None and lot_size < 100:
                remove_reasons.append("Essentially no lot")
            
            if remove_reasons:
                candidates.append({
                    'property': prop,
                    'remove_reasons': remove_reasons,
                    'summary': self.get_property_summary(prop)
                })
        
        return candidates
    
    def auto_remove_properties(self):
        """Automatically remove properties with obvious issues"""
        auto_remove = []
        
        # Properties to automatically remove
        for i, prop in enumerate(self.properties):
            should_remove = False
            reasons = []
            
            # Remove properties with major red flags
            if 'Turk St' in prop['address']:
                should_remove = True
                reasons.append("Turk Street location (rough area)")
            
            # Remove tiny apartments with likely no parking
            lot_size = prop.get('lot_size', 0)
            if lot_size is None:
                lot_size = 0
            if (prop['home_type'] == 'CONDO' and 
                prop['sqft'] < 1100 and 
                ('APT' in prop['address'] or 'UNIT' in prop['address']) and
                lot_size < 100):
                should_remove = True
                reasons.append("Small apartment with no parking")
            
            if should_remove:
                auto_remove.append({
                    'index': i,
                    'property': prop,
                    'reasons': reasons,
                    'summary': self.get_property_summary(prop)
                })
        
        # Remove properties (in reverse order to maintain indices)
        for item in reversed(auto_remove):
            removed_prop = self.properties.pop(item['index'])
            self.removed_properties.append({
                'property': removed_prop,
                'removal_reason': 'Auto-removed: ' + ', '.join(item['reasons'])
            })
        
        return auto_remove
    
    def interactive_filter(self):
        """Interactive filtering interface"""
        print("=== INTERACTIVE PROPERTY FILTER ===")
        print(f"Total properties: {len(self.properties)}")
        
        # First, auto-remove obvious problems
        auto_removed = self.auto_remove_properties()
        if auto_removed:
            print("\n🚫 AUTO-REMOVED PROPERTIES:")
            for item in auto_removed:
                print(f"  - {item['summary']}")
                print(f"    Reason: {', '.join(item['reasons'])}")
        
        print(f"\nRemaining properties: {len(self.properties)}")
        
        # Identify problematic properties
        problematic = self.identify_problematic_properties()
        if problematic:
            print("\n⚠️  PROPERTIES WITH POTENTIAL ISSUES:")
            for i, item in enumerate(problematic):
                print(f"\n{i+1}. {item['summary']}")
                print(f"   Issues: {', '.join(item['issues'])}")
                print(f"   URL: {item['property']['url']}")
                
                response = input("   Remove this property? (y/n/q to quit): ").lower().strip()
                if response == 'q':
                    break
                elif response == 'y':
                    # Find and remove the property
                    for j, prop in enumerate(self.properties):
                        if prop['zpid'] == item['property']['zpid']:
                            removed_prop = self.properties.pop(j)
                            self.removed_properties.append({
                                'property': removed_prop,
                                'removal_reason': 'Manual removal: ' + ', '.join(item['issues'])
                            })
                            print("   ✅ Property removed")
                            break
        
        print(f"\n✅ Filtering complete. {len(self.properties)} properties remaining.")
        return len(self.properties)
    
    def show_manual_candidates(self):
        """Show properties that are good candidates for manual removal"""
        candidates = self.manual_removal_candidates()
        problematic = self.identify_problematic_properties()
        
        print("=== MANUAL REMOVAL CANDIDATES ===")
        print(f"Found {len(candidates)} high-risk properties:")
        
        for i, item in enumerate(candidates):
            print(f"\n{i+1}. {item['summary']}")
            print(f"   Concerns: {', '.join(item['remove_reasons'])}")
            print(f"   URL: {item['property']['url']}")
        
        print(f"\n=== ALL POTENTIALLY PROBLEMATIC PROPERTIES ===")
        print(f"Found {len(problematic)} properties with potential issues:")
        
        for i, item in enumerate(problematic):
            print(f"\n{i+1}. {item['summary']}")
            print(f"   Issues: {', '.join(item['issues'])}")
            print(f"   URL: {item['property']['url']}")
    
    def save_filtered_data(self, output_file=None):
        """Save filtered data to new files"""
        if output_file is None:
            output_file = self.data_file.replace('.json', '_filtered.json')
        
        # Update the scan date
        self.data['scan_date'] = datetime.now().isoformat()
        self.data['properties'] = self.properties
        
        # Save filtered data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        
        # Save removal log
        removal_log = {
            'original_count': len(self.properties) + len(self.removed_properties),
            'filtered_count': len(self.properties),
            'removed_count': len(self.removed_properties),
            'removed_properties': self.removed_properties,
            'filter_date': datetime.now().isoformat()
        }
        
        log_file = output_file.replace('.json', '_removal_log.json')
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(removal_log, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Filtered data saved to: {output_file}")
        print(f"📋 Removal log saved to: {log_file}")
        
        return output_file, log_file

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Manual Property Filter')
    parser.add_argument('--data', default='market_scan_multi_data.json',
                       help='Input JSON data file')
    parser.add_argument('--mode', choices=['interactive', 'show', 'auto'],
                       default='show',
                       help='Filter mode: interactive, show candidates, or auto-remove')
    parser.add_argument('--output', help='Output file for filtered data')
    
    args = parser.parse_args()
    
    # Initialize filter
    filter_tool = PropertyFilter(args.data)
    
    if args.mode == 'interactive':
        filter_tool.interactive_filter()
        filter_tool.save_filtered_data(args.output)
    elif args.mode == 'show':
        filter_tool.show_manual_candidates()
    elif args.mode == 'auto':
        auto_removed = filter_tool.auto_remove_properties()
        print(f"Auto-removed {len(auto_removed)} properties")
        filter_tool.save_filtered_data(args.output)

if __name__ == '__main__':
    main() 