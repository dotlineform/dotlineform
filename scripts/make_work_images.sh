# Minimal usage
# From repo root:
# run this first once to make the script executable:
# chmod +x scripts/make_work_images.sh

# call the script with two optional arguments:
# ./scripts/make_work_images.sh path/to/source_jpgs assets/works/img

#!/usr/bin/env bash
set -euo pipefail

# ---------
# CONFIG
# ---------
INPUT_DIR="${1:-.}"                 # where {work_id}.jpg lives - default = pwd
OUTPUT_DIR="${2:-assets/works/img}"     # where the .webp derivatives are written - default = assets/works/img

# Quality settings (tune if needed)
WEBP_PRESET="photo"
PRIMARY_Q=82
THUMB_Q=78
COMPRESSION_LEVEL=6

mkdir -p "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR/thumbs"

# Check ffmpeg exists
command -v ffmpeg >/dev/null 2>&1 || {
  echo "Error: ffmpeg not found. Install ffmpeg first."
  exit 1
}

# Check optional converters for HEIC/HEIF
HAS_SIPS=0
HAS_HEIF_CONVERT=0
if command -v sips >/dev/null 2>&1; then
  HAS_SIPS=1
fi
if command -v heif-convert >/dev/null 2>&1; then
  HAS_HEIF_CONVERT=1
fi

# Temp folder for any HEIC/HEIF conversions (cleaned on exit)
TMP_DIR=""
cleanup_tmp() {
  if [[ -n "${TMP_DIR}" && -d "${TMP_DIR}" ]]; then
    rm -rf "${TMP_DIR}"
  fi
}
trap cleanup_tmp EXIT

# ---------
# HELPERS
# ---------
make_thumb() {
  local in="$1"
  local size="$2"
  local out="$3"

  # Centre-crop square thumbnail:
  # 1) scale so the *shorter* dimension becomes the target size
  # 2) crop target x target from the centre
  ffmpeg -hide_banner -loglevel error -y \
    -i "$in" \
    -map_metadata -1 \
    -vf "scale='if(gt(iw,ih),-1,${size})':'if(gt(iw,ih),${size},-1)':flags=lanczos,crop=${size}:${size}" \
    -c:v libwebp -preset "$WEBP_PRESET" -q:v "$THUMB_Q" -compression_level "$COMPRESSION_LEVEL" \
    "$out"
}

make_primary() {
  local in="$1"
  local width="$2"
  local out="$3"

  # Resize to target width, preserve aspect ratio, and do NOT upscale
  ffmpeg -hide_banner -loglevel error -y \
    -i "$in" \
    -map_metadata -1 \
    -vf "scale=w='min(iw,${width})':h=-2:flags=lanczos" \
    -c:v libwebp -preset "$WEBP_PRESET" -q:v "$PRIMARY_Q" -compression_level "$COMPRESSION_LEVEL" \
    "$out"
}

# ---------
# RUN
# ---------
shopt -s nullglob
found=0

for src in "$INPUT_DIR"/*.jpg "$INPUT_DIR"/*.JPG "$INPUT_DIR"/*.jpeg "$INPUT_DIR"/*.JPEG "$INPUT_DIR"/*.heic "$INPUT_DIR"/*.HEIC "$INPUT_DIR"/*.heif "$INPUT_DIR"/*.HEIF "$INPUT_DIR"/*.png "$INPUT_DIR"/*.PNG "$INPUT_DIR"/*.tif "$INPUT_DIR"/*.TIF "$INPUT_DIR"/*.tiff "$INPUT_DIR"/*.TIFF; do
  found=1
  fname="$(basename "$src")"
  work_id="${fname%.*}"  # {work_id} from {work_id}.ext

  # Use original source by default; for HEIC/HEIF we convert first due to FFmpeg limitations
  src_use="$src"
  ext="${fname##*.}"
  # macOS ships Bash 3.2 by default; avoid Bash 4 `${var,,}`
  ext_lc="$(printf '%s' "$ext" | tr '[:upper:]' '[:lower:]')"

  if [[ "$ext_lc" == "heic" || "$ext_lc" == "heif" ]]; then
    if [[ "$HAS_SIPS" -eq 1 ]]; then
      [[ -n "$TMP_DIR" ]] || TMP_DIR="$(mktemp -d 2>/dev/null || mktemp -d -t dlf_heic)"
      tmp_jpg="$TMP_DIR/${work_id}.jpg"
      echo "Converting $fname -> $(basename "$tmp_jpg") (sips)"
      # Convert to JPEG (quality 90). Suppress sips stdout noise.
      sips -s format jpeg -s formatOptions 90 "$src" --out "$tmp_jpg" >/dev/null
      src_use="$tmp_jpg"
    elif [[ "$HAS_HEIF_CONVERT" -eq 1 ]]; then
      [[ -n "$TMP_DIR" ]] || TMP_DIR="$(mktemp -d 2>/dev/null || mktemp -d -t dlf_heic)"
      tmp_jpg="$TMP_DIR/${work_id}.jpg"
      echo "Converting $fname -> $(basename "$tmp_jpg") (heif-convert)"
      heif-convert -q 90 "$src" "$tmp_jpg" >/dev/null
      src_use="$tmp_jpg"
    else
      echo "Warning: $fname is HEIC/HEIF but neither 'sips' nor 'heif-convert' is available. Skipping."
      continue
    fi
  fi

  echo "Processing $fname -> $work_id"

  make_thumb  "$src_use" 96  "$OUTPUT_DIR/thumbs/${work_id}-thumb-96.webp"
  make_thumb  "$src_use" 192 "$OUTPUT_DIR/thumbs/${work_id}-thumb-192.webp"
  make_primary "$src_use" 800  "$OUTPUT_DIR/${work_id}-primary-800.webp"
  make_primary "$src_use" 1200 "$OUTPUT_DIR/${work_id}-primary-1200.webp"
  make_primary "$src_use" 1600 "$OUTPUT_DIR/${work_id}-primary-1600.webp"
  make_primary "$src_use" 2400 "$OUTPUT_DIR/${work_id}-primary-2400.webp"
done

if [[ "$found" -eq 0 ]]; then
  echo "No supported image files found in: $INPUT_DIR (jpg/jpeg/heic/heif/png/tif/tiff)"
  exit 1
fi

echo "Done. Primaries written to: $OUTPUT_DIR"
echo "Done. Thumbnails written to: $OUTPUT_DIR/thumbs"