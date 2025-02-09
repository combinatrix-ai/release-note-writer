# Proposal: Remove Docker Dependency from Release Note Writer

## Current Architecture
The Release Note Writer currently uses a Docker-based approach:
1. Builds a Docker image with Python environment
2. Installs dependencies in the container
3. Runs the Python script through a shell entrypoint

## Proposed Changes

### 1. Switch to Composite Action
Replace the Docker-based execution with a composite GitHub Action that will:
- Use GitHub's pre-installed Python
- Set up dependencies using pip
- Execute the script directly

### 2. Required Changes

#### action.yml
```yaml
name: "Release Note Writer"
description: "Generate a release note by comparing git changes using AI"
author: "combinatrix-ai"

inputs:
  compare_to:
    description: "Comparison mode: github_latest (compare with latest GitHub release), auto_tag (find and use latest git tag), or specified (use specific tag)"
    required: false
    default: "github_latest"
  tag:
    description: "Specific git tag to compare with HEAD. Required when compare_to is 'specified'."
    required: false
    default: ""
  model_name:
    description: "Optional model name for generating the release note. Defaults to 'gemini-2.0-flash-thinking-exp-01-21'."
    required: false
    default: "gemini-2.0-flash-thinking-exp-01-21"
  api_key:
    description: "Google Cloud API key for using the model."
    required: true

outputs:
  release_note:
    description: "The generated release note."

runs:
  using: "composite"
  steps:
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.8'
        
    - name: Install dependencies
      shell: bash
      run: |
        python -m pip install --upgrade pip
        pip install prompttrail==0.2.1 requests>=2.31.0 types-requests>=2.31.0

    - name: Generate Release Note
      shell: bash
      env:
        INPUT_COMPARE_TO: ${{ inputs.compare_to }}
        INPUT_TAG: ${{ inputs.tag }}
        INPUT_MODEL_NAME: ${{ inputs.model_name }}
        INPUT_API_KEY: ${{ inputs.api_key }}
        GOOGLE_CLOUD_API_KEY: ${{ inputs.api_key }}
      run: |
        # Create temporary file for output
        TEMP_OUTPUT=$(mktemp)
        
        # Run the Python script
        python ${{ github.action_path }}/release_note_writer.py \
          --compare-to "$INPUT_COMPARE_TO" \
          --tag "$INPUT_TAG" \
          --output "$TEMP_OUTPUT"
        
        # Read and publish the output
        echo "release_note<<EOF" >> $GITHUB_OUTPUT
        cat "$TEMP_OUTPUT" >> $GITHUB_OUTPUT
        echo "EOF" >> $GITHUB_OUTPUT
        
        # Cleanup
        rm "$TEMP_OUTPUT"
```

### 3. Files to Remove
- `Dockerfile`
- `entrypoint.sh`

### 4. Benefits
1. **Faster Execution**
   - No Docker image build time
   - Uses pre-installed Python runtime
   - Direct dependency installation

2. **Simpler Maintenance**
   - Fewer files to maintain
   - No Docker-specific knowledge required
   - Easier to update dependencies

3. **Better Integration**
   - Uses GitHub's native runners
   - Better caching of dependencies
   - More consistent with other GitHub Actions

4. **Reduced Complexity**
   - Removes container layer
   - Simpler debugging
   - More straightforward execution flow

### 5. Implementation Steps
1. Create new action.yml with composite action configuration
2. Remove Docker-related files
3. Update documentation to reflect new setup
4. Test the action in a real workflow
5. Release new version

### 6. Backward Compatibility
The change will be backward compatible as:
- All inputs remain the same
- Output format is unchanged
- Only the execution method changes

### 7. Testing Plan
1. Test with different Python versions (3.8+)
2. Verify all comparison modes work:
   - github_latest
   - auto_tag
   - specified
3. Test with various repository states:
   - With/without tags
   - With/without releases
   - Different types of changes

## Conclusion
Moving to a composite action will simplify the Release Note Writer while maintaining all functionality. The removal of Docker will make the action faster, easier to maintain, and more accessible to contributors.