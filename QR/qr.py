#!/usr/bin/env python3
"""
CTF QR Code Challenge - Complete Setup
Generates QR codes, splits them, creates animated GIF
"""

import qrcode
from PIL import Image
import os

def create_qr_codes():
    """Generate colored QR codes from the challenge words with fixed size"""
    words = [
        "per aspera ad astra",
        "jelas kamu sangat membutuhkan informasi",
        "U2VjdXJpbmV0c3tLaW1hXzlhbF9jaG9j",
        "https://pastebin.com/HQBF32MU",
        "b19rYWxsZWxfcmFob3VfdGZvdWxfYmVoaX0=",
        "https://www.chess.com/forum/view/fun-with-chess/gold-coins-game",
        "https://youtu.be/fB32nZLzM-w?si=zVRf7mqEhpeDJsuE",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=RDdQw4w9WgXcQ&start_radio=1"
    ]
    
    colors = ["red", "green", "blue", "purple", "orange", "cyan", "magenta", "brown"]
    
    # Fixed size for all QR codes
    TARGET_SIZE = 400
    
    print("🎨 Generating QR codes with fixed size...")
    for i, word in enumerate(words, start=1):
        qr = qrcode.QRCode(
            version=None,  # Auto-adjust version
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
            box_size=10,
            border=2  # Smaller border, we'll add padding later
        )
        qr.add_data(word)
        qr.make(fit=True)
        
        # Create QR image
        img = qr.make_image(fill_color=colors[i-1], back_color="white")
        
        # Convert to RGB immediately
        img = img.convert('RGB')
        
        # Resize to fixed size while maintaining aspect ratio
        img.thumbnail((TARGET_SIZE - 40, TARGET_SIZE - 40), Image.LANCZOS)
        
        # Create a white canvas of fixed size
        canvas = Image.new('RGB', (TARGET_SIZE, TARGET_SIZE), 'white')
        
        # Center the QR code on the canvas
        x_offset = (TARGET_SIZE - img.width) // 2
        y_offset = (TARGET_SIZE - img.height) // 2
        canvas.paste(img, (x_offset, y_offset))
        
        canvas.save(f"{i}.png")
        print(f"  ✅ Created {i}.png ({colors[i-1]}) - {TARGET_SIZE}x{TARGET_SIZE}px")
    
    return len(words), TARGET_SIZE

def split_qr_codes(num_qrs, qr_size, parts=4):
    """Split each QR code into horizontal parts"""
    print(f"\n✂️  Splitting QR codes into {parts} parts each...")
    
    part_height = qr_size // parts
    
    for qr_num in range(1, num_qrs + 1):
        img_path = f"{qr_num}.png"
        
        if not os.path.exists(img_path):
            print(f"  ⚠️  Skipping {img_path} (not found)")
            continue
        
        img = Image.open(img_path)
        width, height = img.size
        
        # Verify size
        if width != qr_size or height != qr_size:
            print(f"  ⚠️  Warning: {img_path} has unexpected size {width}x{height}")
        
        for part_num in range(parts):
            y_offset = part_num * part_height
            
            # Crop the part - ensure we get exact part_height
            if part_num == parts - 1:
                # Last part gets whatever remains to avoid rounding issues
                box = (0, y_offset, width, height)
            else:
                box = (0, y_offset, width, y_offset + part_height)
            
            part_img = img.crop(box)
            
            # Save the part
            part_img.save(f"{qr_num}_part_{part_num}.png")
        
        print(f"  ✅ Split {img_path} into {parts} parts ({part_height}px each)")

def create_animated_gif(num_qrs, parts=4, delay=100, output="qr_animation.gif"):
    """Create animated GIF from all QR parts"""
    print(f"\n🎬 Creating animated GIF...")
    
    frames = []
    for qr_num in range(1, num_qrs + 1):
        for part_num in range(parts):
            part_path = f"{qr_num}_part_{part_num}.png"
            if os.path.exists(part_path):
                frames.append(Image.open(part_path))
    
    if frames:
        frames[0].save(
            output,
            save_all=True,
            append_images=frames[1:],
            duration=delay,
            loop=0
        )
        print(f"  ✅ Created {output} with {len(frames)} frames (delay={delay}ms)")
        print(f"  📏 Frame size: {frames[0].size}")
        return output
    else:
        print("  ❌ No frames found to create GIF")
        return None

def cleanup_temp_files(num_qrs, parts=4, keep_gif=True):
    """Clean up temporary files, keep only the GIF"""
    print(f"\n🧹 Cleaning up temporary files...")
    
    files_to_remove = []
    
    # Original QR codes
    for i in range(1, num_qrs + 1):
        files_to_remove.append(f"{i}.png")
    
    # QR parts
    for qr_num in range(1, num_qrs + 1):
        for part_num in range(parts):
            files_to_remove.append(f"{qr_num}_part_{part_num}.png")
    
    removed_count = 0
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            removed_count += 1
    
    print(f"  ✅ Removed {removed_count} temporary files")

def main():
    """Main function to set up the CTF challenge"""
    print("="*60)
    print("🚩 CTF QR Code Challenge Setup")
    print("="*60)
    
    # Step 1: Generate QR codes with fixed size
    num_qrs, qr_size = create_qr_codes()
    
    # Step 2: Split QR codes into parts
    parts_per_qr = 4
    split_qr_codes(num_qrs, qr_size, parts=parts_per_qr)
    
    # Step 3: Create animated GIF
    gif_path = create_animated_gif(
        num_qrs, 
        parts=parts_per_qr, 
        delay=100,  # milliseconds per frame
        output="qr_animation.gif"
    )
    
    # Step 4: Clean up temporary files
    cleanup_temp_files(num_qrs, parts=parts_per_qr)
    
    print("\n" + "="*60)
    print("✨ Challenge Setup Complete!")
    print("="*60)
    if gif_path:
        print(f"📦 Output file: {gif_path}")
        print(f"📏 QR Code size: {qr_size}x{qr_size}px")
        print(f"📊 Total frames: {num_qrs * parts_per_qr}")
        print(f"🎯 Flag: Securinets{{1C4M3154W1C0nQRu3r3D}}")
        print("\n💡 To solve: python solver.py qr_animation.gif")
    else:
        print("❌ Failed to create GIF")

if __name__ == "__main__":
    main()
