# Git workflow

- After completing a requested code change and running the relevant checks, create a Git commit automatically. Do not wait for the user to press the Commit button.
- Stage and commit only files changed for the current task. Preserve pre-existing and unrelated user changes.
- Use a short, descriptive commit message that reflects the completed work.
- After creating the task commit, automatically push the current branch to its configured upstream remote. Do not wait for the user to press the Push button.
- Never force-push. If the push is rejected or the branch has no upstream, stop and explain what is needed instead of changing remote history or configuration implicitly.
- If checks fail or the change is incomplete, do not commit; explain what remains instead.
