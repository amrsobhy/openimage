#!/usr/bin/env python3
"""Cache management utility for the Licensed Image Finder."""

import argparse
import sys
import json
from src.cache import ImageCache


def main():
    """Main function for cache management."""
    parser = argparse.ArgumentParser(
        description='Manage the image search cache'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Stats command
    subparsers.add_parser('stats', help='Show cache statistics')

    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear cache entries')
    clear_parser.add_argument(
        '--expired',
        action='store_true',
        help='Clear only expired entries (default: clear all)'
    )

    # Search command
    search_parser = subparsers.add_parser('search', help='Search cached queries')
    search_parser.add_argument('pattern', help='Search pattern (e.g., "einstein")')

    args = parser.parse_args()

    # Initialize cache
    cache = ImageCache()

    if args.command == 'stats':
        # Show statistics
        stats = cache.get_stats()
        print("\n📊 Cache Statistics")
        print("=" * 50)
        print(f"Total entries:     {stats['total_entries']}")
        print(f"Active entries:    {stats['active_entries']}")
        print(f"Expired entries:   {stats['expired_entries']}")
        print(f"Total cache hits:  {stats['total_hits']}")
        print(f"Avg hits/entry:    {stats['cache_hit_rate']}")
        print(f"Database size:     {stats['db_size_mb']} MB")
        print(f"TTL (days):        {stats['ttl_days']}")

        if stats['popular_queries']:
            print("\n🔥 Most Popular Queries:")
            print("-" * 50)
            for i, query_info in enumerate(stats['popular_queries'][:10], 1):
                print(f"{i}. {query_info['query']} ({query_info['entity_type']}) "
                      f"- {query_info['source']}: {query_info['hits']} hits")

    elif args.command == 'clear':
        if args.expired:
            # Clear only expired entries
            count = cache.clear_expired()
            print(f"\n✓ Cleared {count} expired cache entries")
        else:
            # Confirm before clearing all
            print("\n⚠️  WARNING: This will clear ALL cache entries!")
            response = input("Are you sure? (yes/no): ")
            if response.lower() == 'yes':
                count = cache.clear_all()
                print(f"\n✓ Cleared {count} cache entries")
            else:
                print("\n✗ Cancelled")

    elif args.command == 'search':
        # Search for cached queries
        results = cache.search_cache(args.pattern)

        if results:
            print(f"\n🔍 Found {len(results)} matching cache entries:")
            print("=" * 80)
            for result in results:
                print(f"\nQuery:      {result['query']}")
                print(f"Type:       {result['entity_type']}")
                print(f"Source:     {result['source']}")
                print(f"Hits:       {result['hit_count']}")
                print(f"Created:    {result['created_at']}")
                print(f"Expires:    {result['expires_at']}")
                print("-" * 80)
        else:
            print(f"\n✗ No cache entries found matching '{args.pattern}'")

    else:
        parser.print_help()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
