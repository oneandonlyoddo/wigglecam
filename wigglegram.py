#!/usr/bin/env python3
"""wigglegram.py — Align image sets and create animated wigglegrams.

Dependencies:
    sudo apt install -y python3-opencv
"""

import cv2
import numpy as np


# ── Anchor detection ─────────────────────────────────────────────────────────


def _find_distinct_anchor(gray, cx, cy, search_radius=150, patch_size=64):
    """Locate the most feature-rich point near (cx, cy).

    Uses Shi-Tomasi corner detection inside a search region around the
    requested centre, then selects the corner that best balances feature
    strength and proximity to (cx, cy).

    Returns (ax, ay) — the chosen anchor coordinate.
    """
    h, w = gray.shape
    half = patch_size // 2

    mask = np.zeros((h, w), dtype=np.uint8)
    y_lo = max(half, cy - search_radius)
    y_hi = min(h - half, cy + search_radius)
    x_lo = max(half, cx - search_radius)
    x_hi = min(w - half, cx + search_radius)
    mask[y_lo:y_hi, x_lo:x_hi] = 255

    corners = cv2.goodFeaturesToTrack(
        gray,
        maxCorners=100,
        qualityLevel=0.01,
        minDistance=half,
        mask=mask,
    )

    if corners is None or len(corners) == 0:
        print(f"  [warn] No distinct features near centre — falling back to ({cx}, {cy})")
        return cx, cy

    best, best_score = (cx, cy), -1.0
    n = len(corners)
    for i, c in enumerate(corners):
        px, py = float(c[0, 0]), float(c[0, 1])
        quality = 1.0 - i / n
        dist = np.hypot(px - cx, py - cy)
        proximity = max(0.0, 1.0 - dist / (search_radius * 1.4))
        score = 0.4 * quality + 0.6 * proximity
        if score > best_score:
            best_score = score
            best = (int(round(px)), int(round(py)))

    return best


# ── Template matching with sub-pixel refinement ─────────────────────────────


def _subpixel_peak(corr, ix, iy):
    """Refine an integer peak location in a correlation map to sub-pixel
    accuracy by fitting a 1-D parabola along each axis."""
    h, w = corr.shape
    dx = dy = 0.0

    if 0 < ix < w - 1:
        l, c, r = float(corr[iy, ix - 1]), float(corr[iy, ix]), float(corr[iy, ix + 1])
        denom = 2.0 * c - l - r
        if abs(denom) > 1e-7:
            dx = 0.5 * (l - r) / denom

    if 0 < iy < h - 1:
        t, c, b = float(corr[iy - 1, ix]), float(corr[iy, ix]), float(corr[iy + 1, ix])
        denom = 2.0 * c - t - b
        if abs(denom) > 1e-7:
            dy = 0.5 * (t - b) / denom

    return ix + np.clip(dx, -0.5, 0.5), iy + np.clip(dy, -0.5, 0.5)


def _match_anchor(ref_gray, tgt_gray, ax, ay, patch_size=64, search_margin=300):
    """Match the anchor patch from *ref_gray* inside *tgt_gray*.

    Returns (dx, dy, confidence):
        dx, dy     — translation to apply to the target so its anchor
                     coincides with the reference anchor.
        confidence — normalised cross-correlation peak value (0–1).
    """
    half = patch_size // 2
    h, w = ref_gray.shape

    template = ref_gray[ay - half : ay + half, ax - half : ax + half]

    sy1 = max(0, ay - search_margin)
    sy2 = min(h, ay + search_margin)
    sx1 = max(0, ax - search_margin)
    sx2 = min(w, ax + search_margin)
    search = tgt_gray[sy1:sy2, sx1:sx2]

    if search.shape[0] < template.shape[0] or search.shape[1] < template.shape[1]:
        raise ValueError("Search region is smaller than the anchor patch — try a larger image overlap or smaller patch-size")

    result = cv2.matchTemplate(search, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    sub_x, sub_y = _subpixel_peak(result, max_loc[0], max_loc[1])

    found_x = sx1 + sub_x + half
    found_y = sy1 + sub_y + half

    return ax - found_x, ay - found_y, max_val


# ── Geometric transforms ────────────────────────────────────────────────────


def _translate_image(image, dx, dy):
    """Shift *image* by (dx, dy) pixels using Lanczos interpolation."""
    M = np.float64([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(
        image,
        M,
        (image.shape[1], image.shape[0]),
        flags=cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0),
    )


def _crop_overlap(images, offsets):
    """Crop every frame to the rectangle that is valid in all translated images."""
    h, w = images[0].shape[:2]

    left = int(np.ceil(max(max(0.0, dx) for dx, _ in offsets)))
    right = int(np.floor(w + min(min(0.0, dx) for dx, _ in offsets)))
    top = int(np.ceil(max(max(0.0, dy) for _, dy in offsets)))
    bottom = int(np.floor(h + min(min(0.0, dy) for _, dy in offsets)))

    margin = 2
    left += margin
    top += margin
    right -= margin
    bottom -= margin

    if left >= right or top >= bottom:
        print("  [warn] Overlap region is empty — skipping crop")
        return images

    print(f"  Cropped to {right - left} x {bottom - top}")
    return [img[top:bottom, left:right] for img in images]


def _crop_and_scale(images, target_width, target_height):
    """Crop to aspect ratio then scale to (target_width, target_height)."""
    if not images:
        return images

    h, w = images[0].shape[:2]
    target_aspect = target_width / target_height
    current_aspect = w / h

    if current_aspect > target_aspect:
        new_w = int(h * target_aspect)
        x_offset = (w - new_w) // 2
        cropped = [img[:, x_offset:x_offset + new_w] for img in images]
    elif current_aspect < target_aspect:
        new_h = int(w / target_aspect)
        y_offset = (h - new_h) // 2
        cropped = [img[y_offset:y_offset + new_h, :] for img in images]
    else:
        cropped = images

    return [cv2.resize(img, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)
            for img in cropped]


# ── MP4 output ───────────────────────────────────────────────────────────────


def _save_mp4(frames, path, fps=8, boomerang=True, boomerang_count=3):
    """Write frames to an MP4. Boomerang plays 1-2-3-4-3-2-1-2-… for a
    smooth oscillating 3-D effect."""
    seq = list(frames)
    if boomerang and len(seq) > 2:
        cycle = seq + list(reversed(seq[1:-1]))
        seq = cycle * boomerang_count

    h, w = seq[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps, (w, h))
    for frame in seq:
        writer.write(frame)
    writer.release()


# ── Class ────────────────────────────────────────────────────────────────────


class WigglegramMaker:
    """Align a set of images and encode them as a wigglegram MP4.

    Accepts any number of images (≥ 2).

    Example:
        maker = WigglegramMaker(fps=10)
        maker.generate(["a.jpg", "b.jpg", "c.jpg", "d.jpg"], "out.mp4")
    """

    def __init__(self, patch_size=96, search_radius=150, search_margin=300,
                 fps=8, boomerang=True, boomerang_count=3):
        self.patch_size = patch_size
        self.search_radius = search_radius
        self.search_margin = search_margin
        self.fps = fps
        self.boomerang = boomerang
        self.boomerang_count = boomerang_count

    def generate(self, image_paths, output_path, cx=None, cy=None, resolution=None):
        """Align images and write a wigglegram MP4.

        Args:
            image_paths: Ordered list of image file paths (≥ 2).
            output_path: Destination .mp4 path.
            cx, cy:      Anchor search centre (defaults to image centre).
            resolution:  Optional (width, height) tuple to crop/scale output.

        Returns:
            output_path on success.

        Raises:
            ValueError: If fewer than 2 images are provided or a file can't be read.
        """
        if len(image_paths) < 2:
            raise ValueError(f"Need at least 2 images, got {len(image_paths)}")

        print(f"Loading {len(image_paths)} images...")
        imgs = []
        for p in image_paths:
            img = cv2.imread(str(p))
            if img is None:
                raise ValueError(f"Cannot read image: '{p}'")
            imgs.append(img)
            print(f"  {p}  ({img.shape[1]} x {img.shape[0]})")

        h, w = imgs[0].shape[:2]
        ax_centre = cx if cx is not None else w // 2
        ay_centre = cy if cy is not None else h // 2

        grays = [cv2.cvtColor(im, cv2.COLOR_BGR2GRAY) for im in imgs]

        print("Finding anchor pattern...")
        ax, ay = _find_distinct_anchor(
            grays[0], ax_centre, ay_centre,
            search_radius=self.search_radius,
            patch_size=self.patch_size,
        )
        print(f"  Anchor at ({ax}, {ay})")

        print("Aligning frames...")
        offsets = [(0.0, 0.0)]
        for i in range(1, len(imgs)):
            dx, dy, conf = _match_anchor(
                grays[0], grays[i], ax, ay,
                patch_size=self.patch_size,
                search_margin=self.search_margin,
            )
            offsets.append((dx, dy))
            print(f"  Frame {i + 1}: dx={dx:+.2f}  dy={dy:+.2f}  confidence={conf:.4f}")
            if conf < 0.5:
                print(f"  [warn] Low match confidence for frame {i + 1} — alignment may be poor")

        aligned = [_translate_image(im, dx, dy) for im, (dx, dy) in zip(imgs, offsets)]
        aligned = _crop_overlap(aligned, offsets)

        if resolution is not None:
            target_w, target_h = resolution
            print(f"Cropping and scaling to {target_w}x{target_h}...")
            aligned = _crop_and_scale(aligned, target_w, target_h)

        print("Creating wigglegram...")
        _save_mp4(
            aligned,
            output_path,
            fps=self.fps,
            boomerang=self.boomerang,
            boomerang_count=self.boomerang_count,
        )
        print(f"  Saved {output_path}")
        return output_path
