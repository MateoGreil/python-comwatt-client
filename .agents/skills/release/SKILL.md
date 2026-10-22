---
name: release
description: Use when asked to make or publish a release of python-comwatt-client, bump its package version, or tag a new version. Includes requests such as "fais une release" or "publie une nouvelle version".
---

# Release python-comwatt-client

`origin` is Forgejo; `github` is GitHub (`MateoGreil/python-comwatt-client`). Forgejo is the source of truth. A push mirror may synchronize GitHub's `main` and tags; verify actual refs instead of assuming synchronization or timing.

Publish in this order: **release commit on Forgejo → tag on Forgejo → same commit and tag on GitHub → GitHub release**. Publishing the GitHub release triggers the `publish.yml` workflow (build then PyPI upload). Forgejo gets a tag only, not a release object. Use fast-forward pushes only; never force-push or move an existing tag.

## 1. Inspect synchronization without pushing

Check both remote URLs, CLI authentication (`gh auth status`), and working-tree status. Preserve unrelated changes.

```bash
git fetch origin --tags && git fetch github --tags
git rev-parse main origin/main github/main
gh release view -R MateoGreil/python-comwatt-client --json tagName --jq '.tagName'
```

Choose `release_base`: the newest approved commit containing all three mains. A GitHub PR merge may put `github/main` ahead of Forgejo; Forgejo or local `main` may also be ahead. Use `git merge-base --is-ancestor` to prove fast-forward relationships. If histories diverge, stop and ask the user how to reconcile them.

Use the last published release tag as `previous_tag`; inspect `git log "$previous_tag..$release_base"` and the `__version__` in `comwatt_client/__init__.py` at that base. If there are no changes, report it instead of publishing an empty release.

## 2. Propose and get approval before any push

Propose the version, changes, English release-notes plan, and any required synchronization. Recommend patch for fixes/dependencies, minor for features, major for breaking changes; the user approves the version.

Wait for explicit confirmation **before any remote mutation, including pre-sync pushes**. After approval, proceed without routine confirmation prompts; stop on errors or changed/unexpected refs.

Set `version` to the approved number, `tag="$version"` (bare, no `v` prefix), and retain `release_base` and `previous_tag`. Check that the proposed tag and GitHub release do not already exist, locally or remotely. On a partial previous attempt, report existing artifacts rather than recreating or moving them.

## 3. Synchronize, isolate, and create the release commit

After approval, fast-forward older mains to `release_base`, Forgejo first. For a GitHub merge awaiting reconciliation:

```bash
git push origin "$release_base:refs/heads/main"
```

Verify Forgejo now has the approved base; if GitHub is behind, verify the mirror or fast-forward it manually. Safely fast-forward a clean local `main` as needed, without resetting or stashing unrelated work. Fetch again and verify all three mains match the approved base before editing.

Create a dedicated worktree (verify `.worktrees/` is ignored; otherwise add it to `.git/info/exclude`):

```bash
git worktree add ".worktrees/release-$version" -b "release-$version" "$release_base"
cd ".worktrees/release-$version"
```

Bump only `__version__` in `comwatt_client/__init__.py` (`pyproject.toml` reads it dynamically). Then validate that the package is publishable:

```bash
uv run --with-requirements requirements-dev.txt pytest
uv build
uvx twine check dist/*
```

All tests must pass, and both the sdist and the wheel must be `PASSED` by `twine check` before going further. Review the staged diff for the version-only change and absence of secrets/local artifacts.

```bash
git add comwatt_client/__init__.py
git commit -m "🔖 chore: release v$version"
release_commit=$(git rev-parse HEAD)
```

Use the literal `🔖` emoji, matching release commits in this repository.

## 4. Publish the commit and tag on Forgejo

Recheck remote `main` against `release_base`; if it changed since approval, stop and re-evaluate.

```bash
git push origin HEAD:refs/heads/main
git ls-remote origin refs/heads/main
git tag -a "$tag" -m "Release v$version" "$release_commit"
git push origin "refs/tags/$tag"
git ls-remote origin refs/heads/main "refs/tags/$tag"
```

Verify the commit push succeeded before creating and pushing the tag. Both Forgejo refs must resolve to `release_commit`; stop on failure. The tag is annotated, with the message `Release v$version`, like the repository's existing tags.

## 5. Verify or publish the same refs on GitHub

```bash
git ls-remote github refs/heads/main "refs/tags/$tag"
```

Both must resolve to `release_commit`. If the mirror has not synchronized, push missing refs explicitly, branch first then tag:

```bash
git push github HEAD:refs/heads/main
git push github "refs/tags/$tag"
```

Recheck both remotes. A conflicting existing tag or rejected push is a stop condition, not permission to force-push.

## 6. Publish the GitHub release

Once the tag exists on GitHub, preview the default notes:

```bash
gh api repos/MateoGreil/python-comwatt-client/releases/generate-notes \
  -f tag_name="$tag" -f previous_tag_name="$previous_tag" --jq '.body'
```

This repository's PRs merge on Forgejo: GitHub's generated notes do not identify them. Compare the preview with `git log "$previous_tag..$release_base"` and list the missing entries (each merge commit carries its Forgejo PR number `(#N)`).

```bash
gh release create "$tag" -R MateoGreil/python-comwatt-client \
  --title "v$version" --verify-tag --generate-notes --notes-start-tag "$previous_tag"
```

If entries are missing, write them in English as plain bullets with their PR number in parentheses, in a temporary file outside tracked files, and add it to the command:

```bash
gh release create "$tag" -R MateoGreil/python-comwatt-client \
  --title "v$version" --verify-tag --generate-notes --notes-start-tag "$previous_tag" \
  --notes-file "$NOTES"
```

`gh` prepends the file's content to the generated notes, so the release is created complete in a single call. The title is `v$version` and the tag bare `$version`, matching the repository's existing releases.

## 7. Verify the PyPI publication

The published release triggers `.github/workflows/publish.yml` (build then PyPI upload of `comwatt-client`). Wait for the run to finish and require its success:

```bash
run_id=$(gh run list -R MateoGreil/python-comwatt-client --workflow publish.yml --limit 1 --json databaseId --jq '.[0].databaseId')
gh run watch "$run_id" -R MateoGreil/python-comwatt-client --exit-status
```

Then verify the version is visible on PyPI (the index may take a moment; retry briefly on 404):

```bash
curl -fsS "https://pypi.org/pypi/comwatt-client/$version/json" >/dev/null && echo "PyPI: $version live"
```

If the run fails: leave the release as is, fix, rerun the workflow (`gh run rerun`), and report it. Do not recreate the release.

## 8. Verify and report

Fetch updated refs, safely fast-forward a clean local `main` to the release commit, and check local/Forgejo/GitHub mains and both tags. Read the published release:

```bash
gh release view "$tag" -R MateoGreil/python-comwatt-client --json url,tagName,isDraft,isPrerelease,body
```

and verify its tag, title, notes, and published status.

Report the version, release URL, commit SHA, and synchronization table (local/Forgejo/GitHub mains, tags, PyPI). If the local checkout cannot be updated safely, report that explicitly. Remove the release worktree once published; on failure, retain the workspace for recovery and report the last successful step.
