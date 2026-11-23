Your task is to create new worktree named '$ARGUMENTS' in .trees dir for new tasks.
So our new changes wont affect the current version.

Follow this steps:
1. Check if there is already $ARGUMENTS dir in .trees, if it ask user to choose new name for this task and branch as it alredy been used for other task.
2. Create new git worktree in .trees dir with $ARGUMENT.
3. Symlink .venv dir in the worktree dir.
4. Copy all project files which are necessary (execpt .venv, node_modules, etc)
5. Launch vscode in worktree dir.