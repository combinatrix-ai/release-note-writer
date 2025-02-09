#!/bin/sh -e

# Set the model name and API key for the Python script
export MODEL_NAME="$INPUT_MODEL_NAME"
export GOOGLE_CLOUD_API_KEY="$INPUT_API_KEY"

# Create a temporary file for the output
TEMP_OUTPUT=$(mktemp)

# Run the Python script with the new parameters
python release_note_writer.py \
  --compare-to "$INPUT_COMPARE_TO" \
  --tag "$INPUT_TAG" \
  --output "$TEMP_OUTPUT"

# Read the generated release note
RELEASE_NOTE=$(cat "$TEMP_OUTPUT")

# Clean up the temporary file
rm "$TEMP_OUTPUT"

# Publish the release note as an output
echo "release_note<<EOF" >> "$GITHUB_OUTPUT"
echo "$RELEASE_NOTE" >> "$GITHUB_OUTPUT"
echo "EOF" >> "$GITHUB_OUTPUT"
