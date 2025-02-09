#!/usr/bin/env python
import os
import subprocess
from typing import Optional
import requests

import click
from prompttrail.agent.runners import CommandLineRunner
from prompttrail.agent.templates import (
    AssistantTemplate,
    LinearTemplate,
    SystemTemplate,
    UserTemplate,
)
from prompttrail.agent.user_interface import CLIInterface
from prompttrail.core import Session
from prompttrail.models.google import GoogleConfig, GoogleModel


def get_github_latest_tag() -> Optional[str]:
    """Get the latest release tag from GitHub."""
    try:
        # Extract repo info from git remote
        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            universal_newlines=True,
        ).strip()
        
        # Parse owner and repo from remote URL
        if "github.com" not in remote_url:
            raise click.ClickException("Remote URL is not a GitHub URL")
            
        parts = remote_url.split("github.com/")[-1].replace(".git", "").split("/")
        if len(parts) != 2:
            raise click.ClickException("Could not parse owner and repo from remote URL")
            
        owner, repo = parts

        # Get latest release from GitHub API
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/releases/latest",
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        
        if response.status_code == 200:
            if "tag_name" not in response.json():
                click.echo("Warning: Could not find latest GitHub release, will include all changes", err=True)
                return None
            return response.json()["tag_name"]
        else:
            response.raise_for_status()
            raise
    except (subprocess.CalledProcessError, requests.RequestException) as e:
        raise click.ClickException(f"Error getting latest GitHub release: {e}")


def get_latest_git_tag() -> Optional[str]:
    """Get the latest tag from git log."""
    try:
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            universal_newlines=True,
        ).strip()
        return tag
    except subprocess.CalledProcessError:
        click.echo("Warning: Could not find any git tags, will include all changes", err=True)
        return None


def get_comparison_tag(compare_to: str, specified_tag: str) -> str:
    """
    Determine which tag to use for comparison based on the comparison mode.
    Returns empty string if no valid tag is found (which will result in comparing against the empty tree).
    """
    # Warn if tag is specified but not using 'specified' mode
    if specified_tag and compare_to != "specified":
        click.echo(
            f"Warning: Tag '{specified_tag}' was specified but compare_to mode is '{compare_to}'. "
            "The specified tag will be ignored.",
            err=True
        )

    if compare_to == "specified":
        if not specified_tag:
            raise click.ClickException("Tag must be specified when using 'specified' comparison mode")
        return specified_tag
    elif compare_to == "github_latest":
        tag = get_github_latest_tag()
        if tag:
            return tag
        click.echo("Warning: Could not find latest GitHub release, will include all changes", err=True)
    elif compare_to == "auto_tag":
        tag = get_latest_git_tag()
        if tag:
            return tag
        click.echo("Warning: Could not find any git tags, will include all changes", err=True)
    else:
        raise click.ClickException(f"Unknown comparison mode: {compare_to}")
    return ""


def get_patch(comparison_tag: str) -> str:
    """
    Generate a patch comparing the given tag to HEAD.
    If no tag is provided, compare the empty tree to HEAD (i.e. include all changes).
    """
    # If a tag is provided, use it; otherwise use the empty tree hash
    if comparison_tag.strip():
        diff_from = comparison_tag
    else:
        diff_from = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"  # Empty tree hash in Git

    try:
        patch = subprocess.check_output(
            ["git", "diff", diff_from, "HEAD"],
            universal_newlines=True,
        )
        return patch
    except subprocess.CalledProcessError as e:
        raise click.ClickException(f"Error generating patch from git diff: {e}")


@click.command()
@click.option(
    "--compare-to",
    type=click.Choice(["github_latest", "auto_tag", "specified"]),
    default="github_latest",
    help="How to determine the comparison tag",
)
@click.option(
    "--tag",
    default="",
    help="Specific tag to compare with HEAD (required when using --compare-to=specified)",
)
@click.option("--output", default=None, help="File to write the release note to")
def write_release_note(compare_to: str, tag: str, output: Optional[str]):
    # Determine which tag to compare against
    comparison_tag = get_comparison_tag(compare_to, tag)
    
    # Generate the patch
    patch = get_patch(comparison_tag)

    if not patch.strip():
        raise click.ClickException("No changes found between the comparison point and HEAD.")

    # Build the template for generating the release note
    templates = LinearTemplate(
        [
            SystemTemplate(
                """
                You're given a patch file. Please write the release note based on the changes in the patch file.
                This is an automated API call to generate a release note. Therefore, only emit the content of the release markdown.
                Do not include any markdown code blocks.
                """
            ),
            # Disable Jinja processing as the patch might contain Jinja-like syntax
            UserTemplate(patch, disable_jinja=True),
            AssistantTemplate(),
        ]
    )

    # Retrieve model configuration from environment variables
    model_name = os.environ.get("MODEL_NAME", "gemini-2.0-flash-thinking-exp-01-21")
    api_key = os.environ.get("GOOGLE_CLOUD_API_KEY")
    if not api_key:
        raise click.ClickException(
            "The environment variable GOOGLE_CLOUD_API_KEY is not set."
        )

    model = GoogleModel(
        configuration=GoogleConfig(
            model_name=model_name,
            api_key=api_key,
        )
    )

    runner = CommandLineRunner(
        model=model, template=templates, user_interface=CLIInterface()
    )

    session = runner.run(session=Session(), debug_mode=True)

    release_note = (
        session.messages[-1].content
    )
    if output:
        with open(output, "w") as f:
            f.write(release_note)
    print("Release note:")
    print(release_note)


if __name__ == "__main__":
    write_release_note()
