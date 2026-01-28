#!/usr/bin/env python3
import os
import sys
import argparse
from typing import List, Dict, Optional, Tuple, Set

try:
    from PIL import Image
except ImportError:
    print("Error: The 'Pillow' library is required but not installed.")
    print("Please install it by running: pip install Pillow")
    sys.exit(1)

# Type alias
PathStr = str

class ImageMerger:
    SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif')

    def __init__(self, directory: PathStr = '.'):
        self.directory = directory
        if not os.path.isdir(directory):
            print(f"Error: Directory '{directory}' does not exist.")
            sys.exit(1)

    def collect_files(self, exclude_files: Optional[Set[PathStr]] = None) -> List[PathStr]:
        """Collects all supported image files from the directory."""
        if exclude_files is None:
            exclude_files = set()
            
        all_files = [
            f for f in os.listdir(self.directory) 
            if f.lower().endswith(self.SUPPORTED_EXTENSIONS) 
            and not f.startswith('._')
            and f not in exclude_files
        ]
        return all_files

    def sort_files(self, files: List[PathStr], sort_by: str = 'time') -> List[PathStr]:
        """Sorts files based on creation time or filename."""
        if sort_by == 'name':
            return sorted(files)
        else: # default to time
            def get_creation_time(f: PathStr) -> float:
                filepath = os.path.join(self.directory, f)
                try:
                    stat = os.stat(filepath)
                    return getattr(stat, 'st_birthtime', stat.st_mtime)
                except OSError:
                    return 0.0
            return sorted(files, key=get_creation_time)

    def generate_pdf(self, 
                    files: List[PathStr], 
                    output_path: PathStr, 
                    replacements: Optional[Dict[int, PathStr]] = None) -> bool:
        """
        Generates a PDF from the list of files.
        """
        if not files and not replacements:
            print("No files to process.")
            return False

        # We need a mutable list that represents the final pages
        final_pages: List[PathStr] = list(files)
        
        if replacements:
            for page_num, filename in replacements.items():
                idx = page_num - 1
                if 0 <= idx < len(final_pages):
                    print(f"-> Replacing Page {page_num} ({final_pages[idx]}) with {filename}")
                    final_pages[idx] = filename
                else:
                    print(f"Warning: Replacement page {page_num} is out of range. Skipping.")

        if not final_pages:
            print("Resulting page list is empty.")
            return False

        print(f"\nFinal Page Order ({len(final_pages)} pages):")
        for i, f in enumerate(final_pages):
            print(f" Page {i+1}: {f}")

        # Image processing
        images: List[Image.Image] = []
        base_image: Optional[Image.Image] = None
        
        try:
            for f in final_pages:
                # Resolve full path: if absolute, use it; else join with dir
                if os.path.isabs(f):
                    filepath = f
                else:
                    filepath = os.path.join(self.directory, f)
                    
                try:
                    img = Image.open(filepath)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    if base_image is None:
                        base_image = img
                    else:
                        images.append(img)
                except Exception as e:
                    print(f"Error reading image {filepath}: {e}")
            
            if base_image:
                base_image.save(
                    output_path, 
                    "PDF", 
                    save_all=True, 
                    append_images=images
                )
                print(f"\nSuccessfully created: {output_path}")
                return True
            else:
                print("Error: No valid images found to create PDF.")
                return False
                
        finally:
            if base_image:
                base_image.close()
            for img in images:
                img.close()

def main():
    parser = argparse.ArgumentParser(description="Merge images to PDF (Updated).")
    parser.add_argument("output", nargs="?", default="output.pdf", help="Output PDF filename")
    parser.add_argument("--dir", default=".", help="Source directory containing images")
    parser.add_argument("--replace", nargs="+", help="Replacement rules 'page:filename'")
    parser.add_argument("--sort", choices=['time', 'name'], default='time', help="Sort order")
    
    args = parser.parse_args()
    
    # Parse replacements
    replacements: Dict[int, str] = {}
    replacement_files: Set[str] = set()
    
    if args.replace:
        for rule in args.replace:
            if ":" in rule:
                try:
                    page_str, fname = rule.split(":", 1)
                    replacements[int(page_str)] = fname
                    # Note: we don't add to replacement_files blindly because
                    # replacement file might be external or in the same dir.
                except ValueError:
                    print(f"Invalid rule: {rule}")

    merger = ImageMerger(directory=args.dir)
    
    # 1. Collect files
    files = merger.collect_files()
    
    if not files:
        print(f"No images found in {args.dir}.")
        sys.exit(0)

    # 2. Sort
    sorted_files = merger.sort_files(files, sort_by=args.sort)
    
    # 3. Generate
    success = merger.generate_pdf(sorted_files, args.output, replacements)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
