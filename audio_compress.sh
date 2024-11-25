#!/bin/bash

# Input directory containing .wav files
INPUT_DIR=$1

# Output directories
OGG_DIR="${INPUT_DIR}/ogg"
OPUS_DIR="${INPUT_DIR}/opus"

# Create output directories if they don't exist
mkdir -p "$OGG_DIR" "$OPUS_DIR"

# Loop through all .wav files in the input directory
for wav_file in "$INPUT_DIR"/*.wav; do
    if [[ -f "$wav_file" ]]; then
        base_name=$(basename "$wav_file" .wav)

        # Convert to Ogg Vorbis with highest compression
        ffmpeg -i "$wav_file" -c:a libvorbis -qscale:a 0 "${OGG_DIR}/${base_name}.ogg"

        # Convert to Opus with highest compression
        ffmpeg -i "$wav_file" -c:a libopus -b:a 32k "${OPUS_DIR}/${base_name}.opus"
    fi
done

echo "Conversion complete!"
echo "Ogg files saved in: $OGG_DIR"
echo "Opus files saved in: $OPUS_DIR"
