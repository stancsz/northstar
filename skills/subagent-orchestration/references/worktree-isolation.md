# Git worktree and changeset isolation

> On-demand reference for [Subagent Orchestration](../SKILL.md). Operationalizes the [Northstar task changeset protocol](../../../docs/northstar/adhoc-scm.md) so parallel workers, checkpoints, and independent QA reviews stay synchronized without clobbering user work or accepting stale diffs.

## When to isolate in a Git worktree

- **Single sequential worker with disjoint paths:** Can run directly in the main checkout if its declared write scope does not overlap with parent edits or build artifacts.
- **Parallel write workers or shared build/test outputs:** Must run in isolated Git worktrees so concurrent builds, test runners, or file edits never collide.

## 1. Dirty-state preflight before creating a worktree

A new `git worktree` starts from a committed Git revision—it does **not** carry over uncommitted tracked changes or untracked files from the main working tree.

1. Run `git status --short` and record `BASE_SHA=$(git rev-parse HEAD)` before creating a workspace.
2. If dirty or untracked files exist in the main checkout:
   - **Unrelated user changes:** Leave them untouched in the main checkout (never run `git reset --hard`, `git checkout -- .`, or `git clean -fd` on user state).
   - **Required task inputs:** Commit them to a task branch or explicitly copy the needed task-scoped files into the new worktree before launching the worker.
3. Choose the worktree location and record its cleanup owner before creation. Prefer a subdirectory of the approved external run directory where the Git or app lifecycle supports it. Keep generated output in task scratch. [Artifact storage](../../northstar/references/artifact-storage.md)

   For a Git CLI worktree, use the already allocated `$runDirectory`:

   ```powershell
   $baseSha = (git rev-parse HEAD).Trim()
   $worktreePath = Join-Path $runDirectory 'worktree'
   git worktree add -b "ns/$taskId" $worktreePath $baseSha
   ```

## 2. Draft checkpoint commits and resumable handoffs

A worker handoff that references only an uncommitted diff or a temporary worktree path is fragile if the session interrupts or the worktree is cleaned up.

- **Commit a task checkpoint before handoff or interruption:** Inside the worktree, stage only the authorized write-scope files and create a draft commit:
  ```powershell
  git -C $worktreePath add -- <authorized-paths>
  git -C $worktreePath commit -m "wip($taskId): checkpoint before handoff"
  $candidateCommit = (git -C $worktreePath rev-parse HEAD).Trim()
  $candidateTree = (git -C $worktreePath rev-parse 'HEAD^{tree}').Trim()
  ```
- **Verify scope before review:** Compare actual changed paths against the declared write scope:
  ```powershell
  git -C $worktreePath diff --name-only "$baseSha..$candidateCommit"
  ```
  Contain and revert any out-of-scope file modifications before routing to review or integration.

## 3. Bind Independent QA to exact tree identity

To prevent stale approvals when branches rebase, squash, or move:

1. **Record both Base SHA and Tree SHA in the QA verdict:** A nonauthor [Independent QA](../../independent-qa/SKILL.md) verdict must record:
   - `Base Commit`: `$baseSha`
   - `Candidate Commit`: `$candidateCommit`
   - `Candidate Tree`: `$candidateTree` (`git rev-parse HEAD^{tree}`)
2. **Invalidate stale approvals automatically:**
   - If the candidate's **tree SHA** changes after review, or if the **base commit** moves in a way that touches overlapping scope or invalidates assumptions, the prior QA verdict is **stale**.
   - A squash or fast-forward merge that changes the commit SHA while preserving the exact `$candidateTree` against the same `$baseSha` keeps its approval valid.

## 4. Integrate and clean up safely

1. **Integrate into the target branch:** Cherry-pick, fast-forward, or apply the verified commit into the integration branch, then confirm the resulting tree matches `$candidateTree` (or run the integrated verification suite when combining multiple tasks).
2. **Remove only owned disposable worktrees:** Confirm the candidate commit is integrated or recoverable from the recorded branch and commit. Stop the worker and inspect the worktree for tracked changes, untracked files, and ignored output, including anything the task still needs. Use the host app's lifecycle for app-managed worktrees. For a Git CLI worktree, inspect before invoking the native removal:

   ```powershell
   git -C $worktreePath status --short --ignored=matching --untracked-files=all
   # Review the output and verify any retained files before running the removal.
   git worktree remove $worktreePath
   ```

   If Git refuses because the tree contains changes, inspect and resolve them within scope. Verify removal from both the filesystem and the tool's worktree list. Report blocked cleanup and any remaining bytes. [Storage closeout](../../northstar/references/artifact-storage.md#3-close-out-owned-scratch)
