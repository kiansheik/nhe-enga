#!/bin/bash
# Convert a directory of WAV recordings to compact Opus files.
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <wav-directory>" >&2
    exit 2
fi

# Input directory containing .wav files
INPUT_DIR=$1

# Output directories
OPUS_DIR="${INPUT_DIR}/opus"

# Create output directories if they don't exist
mkdir -p "$OPUS_DIR"

# Loop through all .wav files in the input directory
for wav_file in "$INPUT_DIR"/*.wav; do
    if [[ -f "$wav_file" ]]; then
        base_name=$(basename "$wav_file" .wav)

        # Convert to Opus with highest compression
        ffmpeg -i "$wav_file" -c:a libopus -b:a 32k "${OPUS_DIR}/${base_name}.opus"
    fi
done

echo "Conversion complete!"
echo "Opus files saved in: $OPUS_DIR"
