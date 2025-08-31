#!/usr/bin/env python3
"""demo_semantic_search.py
Demo script showcasing the semantic house search capabilities.
"""

import json
from semantic_house_search import SemanticHouseSearch, load_config

def demo_semantic_queries():
    """Demonstrate various semantic query interpretations"""
    
    # Load default config
    config = load_config("semantic_config.json")
    
    # Demo queries with explanations
    demo_queries = [
        {
            "query": "no one living above me, NOT a fixer-upper",
            "description": "Find properties with no neighbors above and in good condition"
        },
        {
            "query": "quiet, outdoor space, parking",
            "description": "Find peaceful properties with outdoor amenities and parking"
        },
        {
            "query": "move-in ready, city view",
            "description": "Find turnkey properties with scenic city views"
        },
        {
            "query": "not fixer, top floor",
            "description": "Find good condition top floor units"
        }
    ]
    
    print("🧠 Semantic House Search Demo")
    print("=" * 60)
    
    for i, demo in enumerate(demo_queries, 1):
        print(f"\n{i}. Query: '{demo['query']}'")
        print(f"   Description: {demo['description']}")
        
        # Create searcher and interpret query
        searcher = SemanticHouseSearch(config)
        interpreted = searcher.interpret_semantic_query(demo['query'])
        
        print(f"   Interpreted filters:")
        for key, value in interpreted.items():
            if value:  # Only show non-empty values
                print(f"     {key}: {value}")
    
    print(f"\n{'='*60}")
    print("🎯 Key Features Demonstrated:")
    print("   • Natural language query interpretation")
    print("   • Home type preference mapping")
    print("   • Condition preference detection")
    print("   • Feature preference extraction")
    print("   • Exclusion pattern recognition")
    print("   • Semantic scoring and ranking")

def demo_semantic_scoring():
    """Demonstrate semantic scoring for different property types"""
    
    print(f"\n{'='*60}")
    print("📊 Semantic Scoring Demo")
    print("=" * 60)
    
    # Sample properties
    sample_properties = [
        {
            "address": "123 Main St, San Francisco, CA",
            "home_type": "SINGLE_FAMILY",
            "price": 1500000,
            "sqft": 1200,
            "year_built": 2010,
            "lot_size": 3000
        },
        {
            "address": "456 Oak Ave UNIT 5, San Francisco, CA",
            "home_type": "CONDO",
            "price": 1200000,
            "sqft": 1000,
            "year_built": 1995,
            "lot_size": 500
        },
        {
            "address": "789 Pine St UNIT 12, San Francisco, CA",
            "home_type": "CONDO",
            "price": 1100000,
            "sqft": 900,
            "year_built": 2020,
            "lot_size": 400
        }
    ]
    
    # Test query
    query = "no one living above me, NOT a fixer-upper"
    
    # Load config and create searcher
    config = load_config("semantic_config.json")
    searcher = SemanticHouseSearch(config)
    searcher.semantic_query = query
    searcher.interpreted_filters = searcher.interpret_semantic_query(query)
    
    print(f"Query: '{query}'")
    print(f"Interpreted filters: {searcher.interpreted_filters}")
    print()
    
    for prop in sample_properties:
        score, matches, explanations = searcher.calculate_semantic_score(prop)
        print(f"Property: {prop['address']}")
        print(f"  Type: {prop['home_type']}")
        print(f"  Year Built: {prop['year_built']}")
        print(f"  Semantic Score: {score:.2f}")
        print(f"  Matches: {matches}")
        print(f"  Explanations: {explanations}")
        print()

if __name__ == "__main__":
    demo_semantic_queries()
    demo_semantic_scoring()
    
    print(f"\n{'='*60}")
    print("🚀 Ready to Use!")
    print("=" * 60)
    print("Run the semantic search with:")
    print("python3 semantic_house_search.py --query 'no one living above me, NOT a fixer-upper' --price '1.2M-1.75M' --sqft '750-1500'")
    print("\nOr use the config file:")
    print("python3 semantic_house_search.py --config semantic_config.json")
