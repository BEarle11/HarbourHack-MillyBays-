## Coding

**Think before acting.** Models make wrong assumptions and run with them.

- State assumptions explicitly: if uncertain, use your tools to find answers before asking for direction
- Present multiple interpretations when ambiguity exists; don't pick silently
- Push back when a simpler approach exists
- Stop when confused: name what's unclear and ask for clarification

**Simplicity first.** Don't overcomplicate code or APIs.

- No features beyond what was asked
- No abstractions for single-use code
- No speculative flexibility or configurability
- No error handling for impossible scenarios
- If 200 lines could be 50, rewrite it
- Test: would a senior engineer say this is overcomplicated? If yes, simplify

**Surgical changes.** Touch only what you must.

- Don't "improve" adjacent code, comments, or formatting
- Don't refactor things that aren't broken
- Match existing style, even if you'd do it differently
- If you notice unrelated dead code, mention it; don't delete it
- Remove only imports/variables/functions your changes made unused
- Every changed line should trace directly to the user's request

**Goal-driven execution.** Define success criteria, loop until met.

- Transform imperatives into goals: "write a test that reproduces the bug, then make it pass" not "fix the bug"
- Confirm the goal statement with the user before executing non-trivial work
- For multi-step tasks, state a brief plan with verification checkpoints

## Autonomy Guardrails

**Safety rails for destructive actions.**

- Require explicit user approval for external actions: emails sent, commits pushed, configurations changed
- Block irreversible operations until acknowledged: PRs merged, branches deleted, prod deployments
- Validate output against known schemas before accepting results

**Git conventions.**

- Use conventional commit format: type(scope): subject in imperative mood under 72 characters
- One topic per commit, one topic per PR: don't bundle unrelated changes
- Never amend pushed commits; never skip hooks with --no-verify
- Never push from a skill without explicit user request
- Never include Co-Authored-By trailers

**Verification loop.**

These rules are working if you see: fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, clarifying questions before implementation, and clean minimal PRs without drive-by refactoring. When in doubt, relax the rules for trivial tasks; bias toward caution on non-trivial work.

## Writing

**Clarity over decoration.**

- Don't assume the reader shares your tacit knowledge: explain context they can't infer
- Use active voice when who did something matters
- Use concrete, specific terms over abstract or vague language
- Eliminate needless words: short is better when meaning is preserved
- Avoid cliches and prefabricated phrases; say it fresh
- Use plain English when jargon adds nothing
- Say "X succeeded" not "X did not fail": affirmative for affirmative
- Calibrate claims to evidence; don't overstate or understate
- Express coordinate ideas in parallel form
- Keep related words together; wide separation confuses
- Place new or important information at the end of sentences
- Break sentences over 30 words; mix short and long

**Anti-Patterns to Avoid.** These are the tells that mark AI-written prose:

- Don't convert prose into bullets unless it's a genuine list: two items belong in a sentence
- Don't use em or en dashes as casual sentence punctuation
- Don't use emoji characters
- Don't start consecutive sentences with the same word or phrase
- Don't overuse transition crutch-words: "Additionally," "Furthermore," "Moreover," "Therefore," "However"
- Don't close every paragraph with a summary sentence: trust the content
- Use consistent terms; don't redefine abbreviations mid-document
- Use title case for section and subsection headings
- Support factual claims with citations or concrete evidence: don't be handwavy, don't fabricate. Hallucinated content breaks trust instantly.
- Prefer full forms over contractions in formal technical prose

**Escape Hatch.** Break any of these rules sooner than say anything outright barbarous. Rules are guides to clarity, not ends in themselves.

