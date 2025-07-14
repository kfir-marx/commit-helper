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
    # Use the --staged option to get the diff of files in the staging area
    staged_diff = repo.git.diff('--staged')
    if not staged_diff:
        print("No staged files to commit. Please stage your files first.")
        sys.exit(1)
    return staged_diff

def generate_commit_message(diff):
    """
    Generates a commit message using the Gemini Pro API.
    """
    # Load the API key from the .env file
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env file.")
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    # Create a prompt for the model
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
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate a commit message and commit staged files.")
    parser.add_argument('-p', '--approval-needed', action='store_true', help="Prompt for approval before committing.")
    args = parser.parse_args()

    try:
        # Initialize the repository object
        repo = git.Repo(search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        print("Error: This script must be run inside a Git repository.")
        sys.exit(1)

    # Check for untracked files
    untracked_files = repo.untracked_files
    if untracked_files:
        print("Found untracked files:")
        for f in untracked_files:
            print(f"  - {f}")
        
        add_files = input("Do you want to add these files to git? (y/n): ").lower()
        if add_files == 'y':
            repo.git.add(untracked_files)
            print("Files added to the staging area.")
        else:
            print("Please stage the necessary files and run the script again.")
            sys.exit(0)

    # Get the diff of staged files
    staged_diff = get_staged_diff(repo)

    # Generate the commit message
    print("Generating commit message with Gemini Pro...")
    commit_message = generate_commit_message(staged_diff)
    print(f"\nGenerated Commit Message:\n---\n{commit_message}\n---\n")

    # Commit the changes
    if args.approval_needed:
        approval = input("Do you want to commit with this message? (y/n): ").lower()
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