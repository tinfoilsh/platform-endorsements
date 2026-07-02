#!/usr/bin/env python3

import hashlib
from pathlib import Path

def get_file_hash(filepath):
    """Calculate SHA256 hash of a file."""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except FileNotFoundError:
        return None

def get_platforms():
    """Get list of platform directories."""
    platforms_dir = Path('platforms')
    if not platforms_dir.exists():
        return []
    
    platforms = [d.name for d in platforms_dir.iterdir() 
                if d.is_dir() and (d / 'metadata').exists()]
    return sorted(platforms)

def get_metadata_files(platform):
    """Get list of metadata files for a platform."""
    files = []
    
    # Get files from metadata/ subdirectory
    metadata_dir = Path('platforms') / platform / 'metadata'
    if metadata_dir.exists():
        metadata_files = [f"metadata/{f.name}" for f in metadata_dir.iterdir() if f.is_file()]
        files.extend(metadata_files)
    
    # Get metadata.json from platform root
    platform_dir = Path('platforms') / platform
    metadata_json = platform_dir / 'metadata.json'
    if metadata_json.exists():
        files.append('metadata.json')
    
    return sorted(files)

def compare_platforms():
    """Compare metadata files across all platforms."""
    platforms = get_platforms()
    if not platforms:
        print("No platforms found!")
        return
    
    # Get all unique metadata files across platforms
    all_files = set()
    for platform in platforms:
        files = get_metadata_files(platform)
        all_files.update(files)
    
    all_files = sorted(all_files)
    
    # Track platform pairs that match for all files
    platform_matches = {}
    for i, platform1 in enumerate(platforms):
        for j, platform2 in enumerate(platforms):
            if i < j:  # Only check each pair once
                platform_matches[(platform1, platform2)] = True
    
    for filename in all_files:
        print(f"\nFile: {filename}")
        print("-" * (len(filename) + 6))
        
        # Calculate hashes for this file across all platforms
        file_hashes = {}
        for platform in platforms:
            if filename.startswith('metadata/'):
                # File is in the metadata subdirectory
                filepath = Path('platforms') / platform / filename
            else:
                # File is in the platform root (e.g., metadata.json)
                filepath = Path('platforms') / platform / filename
            file_hashes[platform] = get_file_hash(filepath)
        
        # Print platform headers
        print(f"{'':>12}", end="")
        for platform in platforms:
            print(f"{platform:>12}", end="")
        print()
        
        # Print comparison matrix and update match tracking
        for i, platform1 in enumerate(platforms):
            print(f"{platform1:>12}", end="")
            for j, platform2 in enumerate(platforms):
                if file_hashes[platform1] is None or file_hashes[platform2] is None:
                    # File missing in one or both platforms
                    if file_hashes[platform1] is None and file_hashes[platform2] is None:
                        symbol = "?"  # Both missing
                    else:
                        symbol = "✗"  # One missing
                        # Mark this pair as not matching if one has missing files
                        if i < j and (platform1, platform2) in platform_matches:
                            platform_matches[(platform1, platform2)] = False
                        elif j < i and (platform2, platform1) in platform_matches:
                            platform_matches[(platform2, platform1)] = False
                elif file_hashes[platform1] == file_hashes[platform2]:
                    symbol = "✓"  # Match
                else:
                    symbol = "-"  # Different
                    # Mark this pair as not matching if files are different
                    if i < j and (platform1, platform2) in platform_matches:
                        platform_matches[(platform1, platform2)] = False
                    elif j < i and (platform2, platform1) in platform_matches:
                        platform_matches[(platform2, platform1)] = False
                
                print(f"{symbol:>12}", end="")
            print()
    
    # Print matched platform pairs at the end
    matched_pairs = [(p1, p2) for (p1, p2), matches in platform_matches.items() if matches]
    if matched_pairs:
        print("\n" + "="*50)
        print("COMPLETE MATCHES:")
        print("="*50)
        for platform1, platform2 in matched_pairs:
            print(f"Complete match: {platform1} ↔ {platform2}")
    else:
        print("\n" + "="*50)
        print("No complete matches found between any platform pairs.")
        print("="*50)
        
if __name__ == "__main__":
    compare_platforms()
