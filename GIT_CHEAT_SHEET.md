# Git Safety Cheat Sheet (Python + Codespaces)

This file helps you safely save, experiment, recover, and merge your
code.

------------------------------------------------------------------------

## 1. Save a Working Version (Create a Restore Point)

Use when: - Your code runs correctly - Tests pass - Before stopping work

``` bash
git add .
git commit -m "Working version"
git push
```

------------------------------------------------------------------------

## 2. Create a Safe Branch Before Risky Changes

Use when: - Before refactoring - Before adding a new feature - Before
changing many files

``` bash
git checkout -b experiment
```

------------------------------------------------------------------------

## 3. Discard Broken Changes (Not Yet Committed)

Use when: - You edited files - You did NOT commit - Code is broken and
you want last good version back

``` bash
git restore .
```

------------------------------------------------------------------------

## 4. Go Back to Stable Branch

Use when: - You are on `experiment` - You want your safe code back
immediately

``` bash
git checkout main
```

(Use `master` instead of `main` if your branch is named `master`.)

------------------------------------------------------------------------

## 5. Merge Experiment Back Into Main

Use when: - Your experiment works - You want to include it in `main`

``` bash
git checkout main
git merge experiment
git push
```

------------------------------------------------------------------------

## 6. If Merge Fails (Merge Conflict)

### See conflicted files

``` bash
git status
```

### Fix conflicts manually in files, then:

``` bash
git add filename.py
git commit -m "Resolve merge conflict"
```

### Cancel the merge if needed

``` bash
git merge --abort
```

------------------------------------------------------------------------

## 7. Go Back to an Older Good Commit

Use when: - You already committed bad code - You want to return to a
previous working version

``` bash
git log --oneline
git reset --hard COMMIT_ID
git push --force   # only if you work alone
```

------------------------------------------------------------------------

## 8. Full Recovery on New Machine / Codespace

Use when: - New laptop - New Codespace - Total recovery from GitHub

``` bash
git clone https://github.com/your-username/your-repo.git
```

------------------------------------------------------------------------

## Golden Rules

1.  Commit often when code works\
2.  Use branches before risky changes\
3.  Push regularly to GitHub\
4.  Never panic --- Git can always recover your code
