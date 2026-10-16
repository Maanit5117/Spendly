Run a full pre-commit check on the current changes by delegating to two custom subagents.

Steps
Determine the scope:
If the user passed arguments (for example a file name or feature), use that as the scope.
Otherwise, run git status and git diff to find what changed, and use those files as the scope.
If there are no changes, tell the user and stop.
Delegate to both subagents at the same time (do not wait for one before starting the other):
Delegate to the code-reviewer subagent: review the scoped changes for security, correctness, and edge cases.
Delegate to the test-runner subagent: run the pytest suite (scoped tests first, then the full suite) and diagnose any failures.
Wait for both to finish. Do not edit any code yourself while they run.
Combine the results into one report in this format: Verdict: READY TO COMMIT / FIX FIRST
READY TO COMMIT only if tests all passed AND the review has no Critical or Major findings.
Otherwise FIX FIRST.
Tests: one line with passed / failed / skipped counts, then any failures grouped by root cause. Review: Critical and Major findings, each with file, problem, and fix. Mention Minor findings only as a count. Next actions: a short ordered list of what to fix, most important first.
Rules
Report what the subagents actually returned. Never say tests passed or a review is clean unless a subagent reported it.
If a subagent fails to run or cannot be found, say so plainly and report the other one's results. Do not pretend the missing check passed.
Do not apply fixes unless the user asks afterwards.