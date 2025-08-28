#!/usr/bin/env python3
"""
Egyszerű JSON API az öntözési tanácshoz
"""

import json
import sys
import os

# Import the irrigation advisor
sys.path.append(os.path.dirname(__file__))
from irrigation_advisor import get_irrigation_recommendation


def main():
    """Output JSON recommendation"""
    
    try:
        recommendation = get_irrigation_recommendation()
        
        # Pretty print JSON
        print(json.dumps(recommendation, indent=2, ensure_ascii=False))
        
    except Exception as e:
        error_response = {
            'error': f'Hiba történt: {str(e)}',
            'recommendation': 'error',
            'timestamp': None
        }
        print(json.dumps(error_response, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
