#!/usr/bin/env python3
"""
CTF QR Code GIF Solver
Extracts frames from animated GIF, reconstructs QR codes, and decodes them
"""

from PIL import Image
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import os
import sys

def extract_frames_from_gif(gif_path, output_dir="frames"):
    """Extract all frames from an animated GIF"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    gif = Image.open(gif_path)
    frame_count = 0
    
    try:
        while True:
            frame = gif.copy()
            frame.save(f"{output_dir}/frame_{frame_count:03d}.png")
            frame_count += 1
            gif.seek(gif.tell() + 1)
    except EOFError:
        pass
    
    print(f"✅ Extracted {frame_count} frames to {output_dir}/")
    return frame_count

def group_frames_by_qr(frame_dir, parts_per_qr=4):
    """Group frames into QR codes (assuming 4 parts per QR)"""
    frames = sorted([f for f in os.listdir(frame_dir) if f.endswith('.png')])
    total_qrs = len(frames) // parts_per_qr
    
    qr_groups = []
    for i in range(total_qrs):
        start_idx = i * parts_per_qr
        end_idx = start_idx + parts_per_qr
        qr_groups.append(frames[start_idx:end_idx])
    
    return qr_groups

def reconstruct_qr(frame_paths, frame_dir, output_path):
    """Reconstruct a QR code from its horizontal parts"""
    parts = []
    for frame_name in frame_paths:
        img = Image.open(os.path.join(frame_dir, frame_name))
        parts.append(img)
    
    # Get dimensions
    width = parts[0].width
    total_height = sum(part.height for part in parts)
    
    # Create new image
    reconstructed = Image.new('RGB', (width, total_height))
    
    # Paste parts vertically
    y_offset = 0
    for part in parts:
        reconstructed.paste(part, (0, y_offset))
        y_offset += part.height
    
    reconstructed.save(output_path)
    return output_path

def decode_qr(image_path):
    """Decode QR code from image"""
    img = cv2.imread(image_path)
    decoded_objects = decode(img)
    
    if decoded_objects:
        return decoded_objects[0].data.decode('utf-8')
    else:
        # Try with PIL
        pil_img = Image.open(image_path)
        decoded_objects = decode(pil_img)
        if decoded_objects:
            return decoded_objects[0].data.decode('utf-8')
    
    return None

def main(gif_path):
    print(f"🔍 Analyzing GIF: {gif_path}\n")
    
    # Step 1: Extract frames
    frame_dir = "extracted_frames"
    frame_count = extract_frames_from_gif(gif_path, frame_dir)
    
    # Step 2: Group frames (4 parts per QR)
    qr_groups = group_frames_by_qr(frame_dir, parts_per_qr=4)
    print(f"📦 Found {len(qr_groups)} QR codes (assuming 4 parts each)\n")
    
    # Step 3: Reconstruct and decode each QR
    reconstructed_dir = "reconstructed_qrs"
    if not os.path.exists(reconstructed_dir):
        os.makedirs(reconstructed_dir)
    
    results = []
    for i, group in enumerate(qr_groups, start=1):
        print(f"🔨 Reconstructing QR #{i}...")
        output_path = f"{reconstructed_dir}/qr_{i}.png"
        reconstructed_path = reconstruct_qr(group, frame_dir, output_path)
        
        print(f"🔓 Decoding QR #{i}...")
        content = decode_qr(reconstructed_path)
        
        if content:
            print(f"✅ QR #{i}: {content}\n")
            results.append((i, content))
        else:
            print(f"❌ QR #{i}: Failed to decode\n")
            results.append((i, "DECODE_FAILED"))
    
    # Step 4: Summary
    print("\n" + "="*60)
    print("📋 SUMMARY OF ALL QR CODES")
    print("="*60)
    for qr_num, content in results:
        print(f"QR #{qr_num}: {content}")
    
    # Step 5: Look for base64 encoded flag
    print("\n" + "="*60)
    print("🚩 FLAG ANALYSIS")
    print("="*60)
    
    base64_parts = []
    for qr_num, content in results:
        if content and not content.startswith('http'):
            # Check if it looks like base64
            if any(c in content for c in ['=', 'A-Za-z0-9']):
                base64_parts.append(content)
    
    if base64_parts:
        import base64
        print(f"Found potential base64 parts: {base64_parts}")
        combined = ''.join(base64_parts)
        try:
            decoded_flag = base64.b64decode(combined).decode('utf-8')
            print(f"\n🎉 DECODED FLAG: {decoded_flag}")
        except Exception as e:
            print(f"⚠️  Could not decode as base64: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python solver.py <path_to_gif>")
        print("Example: python solver.py qr_animation.gif")
        sys.exit(1)
    
    gif_path = sys.argv[1]
    
    if not os.path.exists(gif_path):
        print(f"❌ Error: File '{gif_path}' not found!")
        sys.exit(1)
    
    main(gif_path)
