"""
VERITAS AI - Copy-Move (Cloning) Forgery Detection Module.

Copy-move forgery involves copying a region of an image and pasting it into
another location in the same image to conceal an object or duplicate a pattern.
This module implements keypoint-based clone detection using ORB/SIFT with
Euclidean spatial displacement filtering and shift-vector clustering.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
import numpy as np
from PIL import Image
import cv2


@dataclass
class CopyMoveResult:
    visualization_image: Image.Image
    clone_mask: Image.Image
    keypoints_detected: int
    matched_pairs_count: int
    clustered_clusters_count: int
    copy_move_detected: bool
    suspicion_score: float  # 0.0 to 1.0
    forensic_interpretation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "keypoints_detected": self.keypoints_detected,
            "matched_pairs_count": self.matched_pairs_count,
            "clustered_clusters_count": self.clustered_clusters_count,
            "copy_move_detected": self.copy_move_detected,
            "suspicion_score": round(self.suspicion_score, 3),
            "forensic_interpretation": self.forensic_interpretation,
        }


def detect_copy_move(
    image: Image.Image,
    min_spatial_distance: float = 35.0,
    cluster_threshold: int = 4,
    max_keypoints: int = 1500,
) -> CopyMoveResult:
    """
    Detects duplicate / cloned visual structures within the same image.

    Args:
        image: Source PIL Image.
        min_spatial_distance: Minimum pixel distance between candidate cloned pairs
                              to filter out trivial neighboring texture matches.
        cluster_threshold: Minimum number of consistent translation vectors required
                           to flag a verified copy-move cluster.
        max_keypoints: Maximum number of feature points to extract.

    Returns:
        CopyMoveResult with marked visualization image, mask, and metrics.
    """
    # Convert PIL Image to OpenCV BGR and Grayscale
    img_rgb = np.asarray(image.convert("RGB"))
    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Initialize feature detector (try SIFT first, fallback to ORB)
    try:
        detector = cv2.SIFT_create(nfeatures=max_keypoints)
        use_sift = True
    except (AttributeError, cv2.error):
        detector = cv2.ORB_create(nfeatures=max_keypoints)
        use_sift = False

    keypoints, descriptors = detector.detectAndCompute(gray, None)

    if descriptors is None or len(keypoints) < 10:
        # Insufficient texture/features to assess
        empty_mask = Image.new("L", (w, h), 0)
        return CopyMoveResult(
            visualization_image=image.copy(),
            clone_mask=empty_mask,
            keypoints_detected=len(keypoints) if keypoints else 0,
            matched_pairs_count=0,
            clustered_clusters_count=0,
            copy_move_detected=False,
            suspicion_score=0.0,
            forensic_interpretation=(
                "Insufficient distinctive visual keypoints found in this image (e.g. very blurry, "
                "solid color, or low contrast). Copy-move analysis is inconclusive."
            ),
        )

    # Match descriptors against themselves using k-NN with k=2
    if use_sift:
        matcher = cv2.BFMatcher(cv2.NORM_L2)
    else:
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING)

    # Query all descriptors against database of same descriptors
    matches = matcher.knnMatch(descriptors, descriptors, k=2)

    valid_pairs: List[Tuple[cv2.KeyPoint, cv2.KeyPoint, float, float]] = []
    vectors: List[Tuple[float, float]] = []

    for m in matches:
        if len(m) < 2:
            continue
        # In self-matching, m[0] is the point itself (distance 0).
        # m[1] is the closest distinct point in feature space.
        match_candidate = m[1]
        query_idx = match_candidate.queryIdx
        train_idx = match_candidate.trainIdx

        if query_idx >= train_idx:
            # Avoid duplicate symmetric pairs (A->B and B->A)
            continue

        pt1 = keypoints[query_idx].pt
        pt2 = keypoints[train_idx].pt

        dx = pt2[0] - pt1[0]
        dy = pt2[1] - pt1[1]
        dist = np.hypot(dx, dy)

        # Filter out points that are too physically close to each other
        if dist >= min_spatial_distance:
            # Check descriptor distance threshold
            dist_threshold = 180.0 if use_sift else 55.0
            if match_candidate.distance < dist_threshold:
                valid_pairs.append((keypoints[query_idx], keypoints[train_idx], dx, dy))
                vectors.append((dx, dy))

    # Cluster translation vectors (detect consistent spatial shift)
    clustered_pairs: List[Tuple[cv2.KeyPoint, cv2.KeyPoint]] = []
    cluster_count = 0

    if len(vectors) >= cluster_threshold:
        vecs = np.array(vectors)
        # Spatial shift binning into 20-pixel displacement bins
        bin_size = 25.0
        binned_x = np.round(vecs[:, 0] / bin_size)
        binned_y = np.round(vecs[:, 1] / bin_size)
        keys = list(zip(binned_x, binned_y))

        from collections import Counter
        counts = Counter(keys)

        for (bx, by), cnt in counts.items():
            if cnt >= cluster_threshold:
                cluster_count += 1
                # Collect pairs belonging to this spatial translation cluster
                for idx, (k1, k2, dx, dy) in enumerate(valid_pairs):
                    if keys[idx] == (bx, by):
                        clustered_pairs.append((k1, k2))

    # Render forensic visualization on copy of original image
    vis_bgr = img_bgr.copy()
    mask = np.zeros((h, w), dtype=np.uint8)

    # Draw all valid candidate matches in subtle cyan
    for k1, k2, _, _ in valid_pairs:
        p1 = (int(k1.pt[0]), int(k1.pt[1]))
        p2 = (int(k2.pt[0]), int(k2.pt[1]))
        cv2.circle(vis_bgr, p1, 3, (220, 200, 0), -1)
        cv2.circle(vis_bgr, p2, 3, (220, 200, 0), -1)

    # Highlight verified clustered copy-move pairs in high-visibility bright magenta/red
    is_detected = len(clustered_pairs) >= cluster_threshold and cluster_count > 0

    for k1, k2 in clustered_pairs:
        p1 = (int(k1.pt[0]), int(k1.pt[1]))
        p2 = (int(k2.pt[0]), int(k2.pt[1]))
        # Draw connecting line
        cv2.line(vis_bgr, p1, p2, (0, 70, 255), 2, cv2.LINE_AA)
        # Highlight endpoints
        cv2.circle(vis_bgr, p1, 6, (0, 255, 255), 2)
        cv2.circle(vis_bgr, p2, 6, (0, 0, 255), 2)
        # Stamp on localization mask
        cv2.circle(mask, p1, 18, 255, -1)
        cv2.circle(mask, p2, 18, 255, -1)

    # Compute continuous suspicion score (0.0 to 1.0)
    if is_detected:
        suspicion_score = min(0.65 + 0.05 * min(len(clustered_pairs), 7), 0.99)
        interpretation = (
            f"Strong evidence of Copy-Move manipulation detected. Found {len(clustered_pairs)} paired "
            f"keypoints across {cluster_count} coherent translation cluster(s). Identical visual patterns "
            "appear duplicated at different spatial coordinates with matching geometry."
        )
    elif len(valid_pairs) > 15:
        suspicion_score = 0.35
        interpretation = (
            f"Detected {len(valid_pairs)} candidate feature pairs with similar descriptors, but they lack "
            "rigid geometric translation clustering. Likely natural repetitive textures (e.g. foliage, windows, grass)."
        )
    else:
        suspicion_score = 0.05
        interpretation = (
            "No coherent cloned keypoint clusters detected. Feature distribution across the image canvas "
            "is consistent with authentic non-duplicated scenery."
        )

    # Convert back to PIL Image
    vis_rgb = cv2.cvtColor(vis_bgr, cv2.COLOR_BGR2RGB)
    vis_pil = Image.fromarray(vis_rgb)
    mask_pil = Image.fromarray(mask, mode="L")

    return CopyMoveResult(
        visualization_image=vis_pil,
        clone_mask=mask_pil,
        keypoints_detected=len(keypoints),
        matched_pairs_count=len(valid_pairs),
        clustered_clusters_count=cluster_count,
        copy_move_detected=is_detected,
        suspicion_score=float(suspicion_score),
        forensic_interpretation=interpretation,
    )
