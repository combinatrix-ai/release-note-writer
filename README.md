# Release Note Writer 🚀

A GitHub Action that automatically crafts release notes from git diffs using AI! 🤖✨

## Features

- **Smart Diff Analysis**: Compares your latest changes with previous tags or entire history
- **AI-Powered Writing**: Transforms technical diffs into clear, structured markdown release notes
- **GitHub Actions Integration**: Seamlessly fits into your workflow

## Quick Start

### Prerequisites

- GitHub repository with commits
- [Google Cloud API key](https://cloud.google.com/)
- GitHub Actions enabled

### Usage

Basic workflow:

```yaml
steps:
  - uses: actions/checkout@v4
  - name: Generate Release Note
    id: generate-release-note
    uses: combinatrix-ai/release-note-writer@v1
    with:
      api_key: ${{ secrets.GOOGLE_CLOUD_API_KEY }}
```

This set `compare_to: "github_latest"` by default.
This will find latest release on github and compare it to current repo (HEAD).

```yaml
steps:
  - uses: actions/checkout@v4
  - name: Generate Release Note
    id: generate-release-note
    uses: combinatrix-ai/release-note-writer@v1
    with:
      compare_to: specified
      tag: v0.1.0
      api_key: ${{ secrets.GOOGLE_CLOUD_API_KEY }}
```

If you set `compare_to` to `specified`, you must set `tag` too.
On this configuration, v0.1.0 to HEAD is compared.

If you set `compare_to` as `auto_tag`, the action look back `git log` and find latest tag and compare to them.
If you use tag as solely for release purpose and all the release is on the same branch, this is convinient.

The generated release note is available in the `release_note` output, which you can use in many ways! For example:

```yaml
  # Save to a file
  - name: Save Release Note
    run: echo "${{ steps.generate-release-note.outputs.release_note }}" > release_note.md

  # Or use with GitHub's release action
  - name: Create GitHub Release
    uses: softprops/action-gh-release@v1  # Third-party action
    env:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    with:
      tag_name: ${{ github.ref }}
      body: ${{ steps.generate-release-note.outputs.release_note }}

  # Or use in your own custom release process!
```

### Configuration

| Input | Description | Default |
|-------|-------------|---------|
| `compare_to` | One of `github_latest`, `auto_tag`, or `specified` | github_latest |
| `tag` | Tag to compare with `HEAD`, used when `specified` | `""` (All commits) |
| `model_name` | AI model for generation | `gemini-2.0-flash-thinking-exp-01-21` |
| `api_key` | **Required** Google Cloud API key | N/A |

### Output

| Name | Description |
|------|-------------|
| `release_note` | Generated release note in markdown |

## Contributing

Have ideas? Found bugs? Want to add features? We'd love your help! Open an issue or send a pull request to make release notes even better. 💪

## License

[MIT License](LICENSE)
