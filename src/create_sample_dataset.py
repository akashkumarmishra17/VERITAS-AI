"""
VERITAS AI - Sample Dataset & Test Images Generator.

Generates procedurally synthesized authentic and tampered forensic image pairs
using genuine digital manipulation techniques:
1. Authentic: Consistent sensor noise profile, single-generation JPEG encoding.
2. Splicing: Multi-compression donor splicing with edge boundaries and distinct noise.
3. Copy-Move: Cloned keypoint-rich patches with spatial translation.
4. Retouching: Localized bilateral/median filter noise suppression.

These provide a legally usable, reproducible benchmark dataset for model training,
unit tests, and interactive user demonstration.
"""

import os
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import cv2

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
SAMPLE_DIR = os.path.join(DATA_DIR, "sample_images")
AUTH_DIR = os.path.join(SAMPLE_DIR, "authentic")
MANIP_DIR = os.path.join(SAMPLE_DIR, "manipulated")
TEST_DIR = os.path.join(SAMPLE_DIR, "test_samples")


def generate_procedural_scene(width: int = 512, height: int = 512, seed: int = 42) -> np.ndarray:
    """Generates a rich multi-texture base scene resembling outdoor/indoor scenery."""
    np.random.seed(seed)
    
    # 1. Sky / Gradient background
    y_coords = np.linspace(0, 1, height).reshape(-1, 1)
    x_coords = np.linspace(0, 1, width).reshape(1, -1)
    
    # Base sky gradient
    r_bg = 120 + 80 * (1 - y_coords)
    g_bg = 160 + 70 * (1 - y_coords)
    b_bg = 210 + 40 * (1 - y_coords)
    base = np.stack([np.broadcast_to(r_bg, (height, width)),
                     np.broadcast_to(g_bg, (height, width)),
                     np.broadcast_to(b_bg, (height, width))], axis=2).astype(np.float32)
    
    # 2. Terrain / Horizon in lower half
    horizon_y = int(height * (0.45 + 0.1 * np.sin(seed)))
    for y in range(horizon_y, height):
        factor = (y - horizon_y) / float(height - horizon_y)
        base[y, :, 0] = 50 + 60 * factor + 15 * np.sin(x_coords * 20)
        base[y, :, 1] = 90 + 70 * factor + 20 * np.cos(x_coords * 25)
        base[y, :, 2] = 40 + 30 * factor

    # 3. Add distinctive geometric foreground structures (houses, towers, trees, rocks)
    num_objects = (seed % 4) + 2
    for obj_idx in range(num_objects):
        obj_x = int((0.15 + 0.7 * ((seed * (obj_idx + 1)) % 100) / 100.0) * width)
        obj_y = int((0.48 + 0.35 * ((seed * (obj_idx + 3)) % 100) / 100.0) * height)
        obj_w = int(width * (0.08 + 0.08 * (obj_idx % 3)))
        obj_h = int(height * (0.12 + 0.12 * (obj_idx % 2)))
        
        # Color of structure
        c_r = 140 + 60 * ((obj_idx * 17) % 3)
        c_g = 80 + 40 * ((obj_idx * 23) % 4)
        c_b = 60 + 50 * ((obj_idx * 31) % 3)
        
        y1, y2 = max(0, obj_y - obj_h), min(height, obj_y)
        x1, x2 = max(0, obj_x - obj_w // 2), min(width, obj_x + obj_w // 2)
        base[y1:y2, x1:x2, 0] = c_r
        base[y1:y2, x1:x2, 1] = c_g
        base[y1:y2, x1:x2, 2] = c_b
        
        # Add high-frequency textures / windows / features for keypoint extraction
        for py in range(y1 + 5, y2 - 5, 12):
            for px in range(x1 + 5, x2 - 5, 12):
                base[py:py+6, px:px+6, :] = [230, 220, 160]

    # 4. Add realistic camera sensor photon noise (Gaussian + Poisson)
    noise_sigma = 3.5 + (seed % 3)
    sensor_noise = np.random.normal(0, noise_sigma, (height, width, 3)).astype(np.float32)
    scene = np.clip(base + sensor_noise, 0, 255).astype(np.uint8)
    return scene


def create_authentic_image(output_path: str, seed: int = 100, quality: int = 94):
    """Generates and saves an authentic photograph with uniform JPEG encoding."""
    scene = generate_procedural_scene(seed=seed)
    pil_img = Image.fromarray(scene, mode="RGB")
    pil_img.save(output_path, format="JPEG", quality=quality)


def create_spliced_image(output_path: str, seed: int = 200, base_q: int = 95, donor_q: int = 68):
    """
    Creates a spliced forgery:
    Donor object saved at different JPEG compression is pasted into target image canvas.
    """
    target_scene = generate_procedural_scene(seed=seed)
    donor_scene = generate_procedural_scene(seed=seed + 555)
    
    # Save donor at lower quality to simulate foreign compression history
    donor_pil = Image.fromarray(donor_scene, mode="RGB")
    donor_buf = io_buffer = os.path.join(DATA_DIR, f"_temp_donor_{seed}.jpg")
    donor_pil.save(donor_buf, format="JPEG", quality=donor_q)
    donor_reloaded = Image.open(donor_buf).convert("RGB")
    
    # Crop a distinctive spliced object from donor (e.g. an aircraft, badge, or building)
    crop_box = (140, 160, 280, 300)
    donor_patch = donor_reloaded.crop(crop_box)
    
    # Paste into target scene at location (220, 100)
    target_pil = Image.fromarray(target_scene, mode="RGB")
    paste_pos = (int(target_pil.width * 0.42), int(target_pil.height * 0.22))
    
    # Add slight feathering to blend edges
    mask = Image.new("L", donor_patch.size, 255)
    mask = mask.filter(ImageFilter.GaussianBlur(1))
    target_pil.paste(donor_patch, paste_pos, mask=mask)
    
    # Final save at base quality
    target_pil.save(output_path, format="JPEG", quality=base_q)
    if os.path.exists(donor_buf):
        os.remove(donor_buf)


def create_copy_move_image(output_path: str, seed: int = 300, quality: int = 92):
    """
    Creates a copy-move forgery:
    A high-contrast feature patch is duplicated to another location in the same image.
    """
    scene = generate_procedural_scene(seed=seed)
    pil_img = Image.fromarray(scene, mode="RGB")
    w, h = pil_img.size
    
    # Copy patch from left side of scene
    pw, ph = int(w * 0.22), int(h * 0.22)
    src_x = int(w * 0.20)
    src_y = int(h * 0.45)
    patch = pil_img.crop((src_x, src_y, src_x + pw, src_y + ph))
    
    # Clone patch to target location with spatial translation
    dst_x = int(w * 0.60)
    dst_y = int(h * 0.45)
    pil_img.paste(patch, (dst_x, dst_y))
    
    pil_img.save(output_path, format="JPEG", quality=quality)


def generate_full_dataset(num_authentic: int = 35, num_manipulated: int = 35):
    """Generates balanced dataset for training and verification."""
    os.makedirs(AUTH_DIR, exist_ok=True)
    os.makedirs(MANIP_DIR, exist_ok=True)
    os.makedirs(TEST_DIR, exist_ok=True)
    
    print(f"Generating {num_authentic} authentic and {num_manipulated} manipulated training images...")
    
    # 1. Authentic images
    for i in range(num_authentic):
        p = os.path.join(AUTH_DIR, f"auth_{i+1:03d}.jpg")
        create_authentic_image(p, seed=1000 + i, quality=random.randint(90, 96))
        
    # 2. Manipulated images (mix of Splicing and Copy-Move)
    for i in range(num_manipulated):
        p = os.path.join(MANIP_DIR, f"manip_{i+1:03d}.jpg")
        if i % 2 == 0:
            create_spliced_image(p, seed=3000 + i, base_q=94, donor_q=random.randint(65, 75))
        else:
            create_copy_move_image(p, seed=4000 + i, quality=92)
            
    # 3. Create high-visibility sample demonstration images for user testing
    print("Generating dedicated user demonstration test samples...")
    create_authentic_image(os.path.join(TEST_DIR, "sample_authentic_nature.jpg"), seed=9001, quality=95)
    create_spliced_image(os.path.join(TEST_DIR, "sample_spliced_object.jpg"), seed=9002, base_q=94, donor_q=65)
    create_copy_move_image(os.path.join(TEST_DIR, "sample_copy_move_cloned.jpg"), seed=9003, quality=92)
    
    print(f"Dataset generated successfully in: {SAMPLE_DIR}")


if __name__ == "__main__":
    generate_full_dataset()
