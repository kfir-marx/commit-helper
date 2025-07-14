#!/usr/bin/env python3

import os
import sys
import argparse
import git
import google.generativeai as genai
from dotenv import load_dotenv

def get_staged_diff(repo):
    """
    Gets the diff of staged files in the repository.
    """
    staged_diff = repo.git.diff('--staged')
    if not staged_diff:
        print("No changes to commit. All tracked files are up to date.")
        sys.exit(0) # Exit gracefully if there's nothing to do
    return staged_diff

def generate_commit_message(diff):
    """
    Generates a commit message using the Gemini Pro API.
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found. Ensure it's in a .env file in the repository's root.")
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""
    Based on the following git diff, please generate a concise and descriptive commit message.
    The message should follow the conventional commit format (e.g., 'feat: add user authentication').

    Diff:
    {diff}
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating commit message: {e}")
        sys.exit(1)

def main():
    """
    Main function to run the git-commit-helper script.
    """
    parser = argparse.ArgumentParser(description="Automate staging and commit message generation.")
    parser.add_argument('-p', '--approval-needed', action='store_true', help="Prompt for approval before committing.")
    args = parser.parse_args()

    try:
        repo = git.Repo(search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        print("Error: This script must be run inside a Git repository.")
        sys.exit(1)

    modified_files = [item.a_path for item in repo.index.diff(None)]
    if modified_files:
        print("Found modified files. Staging them automatically:")
        for f in modified_files:
            print(f"  - {f}")
        repo.git.add(modified_files)
        print("Modified files staged.")

    # Check for untracked files
    untracked_files = repo.untracked_files
    if untracked_files:
        print("\nFound untracked files:")
        for f in untracked_files:
            print(f"  - {f}")
        
        add_files = input("Do you want to add these files to git? (y/n): ").lower()
        if add_files == 'y':
            repo.git.add(untracked_files)
            print("New files added to the staging area.")
        else:
            print("Untracked files were not added.")

    # Get the diff of all staged files
    staged_diff = get_staged_diff(repo)

    # Generate the commit message
    print("\nGenerating commit message with Gemini...")
    commit_message = generate_commit_message(staged_diff)
    print(f"\nGenerated Commit Message:\n---\n{commit_message}\n---")

    # Commit the changes
    if args.approval_needed:
        approval = input("\nDo you want to commit with this message? (y/n): ").lower()
        if approval == 'y':
            repo.index.commit(commit_message)
            print("Changes committed successfully! 🎉")
        else:
            print("Commit aborted.")
    else:
        repo.index.commit(commit_message)
        print("Changes committed successfully! 🎉")

if __name__ == "__main__":
    main()