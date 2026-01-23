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

# Check ffmpeg exists
command -v ffmpeg >/dev/null 2>&1 || {
  echo "Error: ffmpeg not found. Install ffmpeg first."
  exit 1
}

# ---------
# HELPERS
# ---------
make_thumb() {
  local in="$1"
  local out="$2"

  # Centre-crop square thumbnail:
  # 1) scale so the *shorter* dimension becomes 480
  # 2) crop 480x480 from the centre
  ffmpeg -hide_banner -loglevel error -y \
    -i "$in" \
    -map_metadata -1 \
    -vf "scale='if(gt(iw,ih),-1,480)':'if(gt(iw,ih),480,-1)':flags=lanczos,crop=480:480" \
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

for src in "$INPUT_DIR"/*.jpg "$INPUT_DIR"/*.JPG "$INPUT_DIR"/*.jpeg "$INPUT_DIR"/*.JPEG; do
  found=1
  fname="$(basename "$src")"
  work_id="${fname%.*}"  # {work_id} from {work_id}.jpg

  echo "Processing $fname -> $work_id"

  make_thumb  "$src" "$OUTPUT_DIR/${work_id}-thumb-480.webp"
  make_primary "$src" 800  "$OUTPUT_DIR/${work_id}-primary-800.webp"
  make_primary "$src" 1200 "$OUTPUT_DIR/${work_id}-primary-1200.webp"
  make_primary "$src" 1600 "$OUTPUT_DIR/${work_id}-primary-1600.webp"
  make_primary "$src" 2400 "$OUTPUT_DIR/${work_id}-primary-2400.webp"
done

if [[ "$found" -eq 0 ]]; then
  echo "No .jpg/.jpeg files found in: $INPUT_DIR"
  exit 1
fi

echo "Done. Output written to: $OUTPUT_DIR"