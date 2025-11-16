#!/usr/bin/env python3
"""Main entry point for the Licensed Image Finder."""

import sys
import json
import argparse
from src.image_finder import LicensedImageFinder
from src.config import Config


def main():
    """Main function to run the image finder from command line."""
    parser = argparse.ArgumentParser(
        description='Find high-quality, license-safe images for commercial use'
    )
    parser.add_argument(
        'query',
        type=str,
        help='Search query (e.g., person name, entity)'
    )
    parser.add_argument(
        '--entity-type',
        type=str,
        default='person',
        choices=['person', 'place', 'thing', 'other'],
        help='Type of entity (default: person)'
    )
    parser.add_argument(
        '--max-results',
        type=int,
        default=20,
        help='Maximum number of results to return (default: 20)'
    )
    parser.add_argument(
        '--no-face-filter',
        action='store_true',
        help='Disable face detection filter for person entities'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show status of available sources and exit'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (JSON format). If not specified, prints to stdout'
    )

    args = parser.parse_args()

    # Initialize the image finder
    finder = LicensedImageFinder()

    # Show status if requested
    if args.status:
        status = finder.get_status()
        print(json.dumps(status, indent=2))
        return 0

    # Search for images
    print(f"Searching for '{args.query}' (entity type: {args.entity_type})...", file=sys.stderr)
    print(f"Available sources: {', '.join(finder.get_available_sources())}", file=sys.stderr)

    require_face = args.entity_type == 'person' and not args.no_face_filter

    results = finder.find_images(
        query=args.query,
        entity_type=args.entity_type,
        max_results=args.max_results,
        require_face=require_face
    )

    # Prepare output
    output_data = {
        'query': args.query,
        'entity_type': args.entity_type,
        'total_results': len(results),
        'face_filter_applied': require_face,
        'images': results
    }

    # Write output
    output_json = json.dumps(output_data, indent=2)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_json)
        print(f"\nResults saved to {args.output}", file=sys.stderr)
    else:
        print(output_json)

    print(f"\nFound {len(results)} high-quality, license-safe images", file=sys.stderr)

    return 0


if __name__ == '__main__':
    sys.exit(main())
