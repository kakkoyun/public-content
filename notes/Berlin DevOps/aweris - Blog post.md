### BLOG DUMB

## The Problem

### The Limitations of Remote-Only Workflow Execution in GitHub Actions

While GitHub Actions brings automation and CI/CD seamlessly into the GitHub platform, it has its drawbacks, primarily the inability to execute workflows locally. This limitation has implications:

1. **Duplicate Effort**: Developers often maintain separate workflows for local and GitHub Actions-based tasks like building, testing, and linting.

2. **Cost of Time and Resources**: Running workflows on GitHub consumes action minutes and requires pushing changes to remote repositories to trigger tests. Testing some triggers can be quite challenging due to the specific triggering conditions required for the events to occur.

3. **Extended Feedback Loop**: The absence of local testing elongates the feedback loop, requiring developers to commit, push, and await remote execution to assess the success of their changes.

4. **Debugging Difficulties**: Investigating workflow failures becomes a daunting task without the option for local debugging.

5. **Limited Testing of Trigger Events:** Testing Github Actions workflows taht depend on specific trigger events(like pull request, issues or tags) can be cumbersome. Simulating these events often requires elaborate setup or workarounds, which can be inefficient and error-prone.

### Push and Pray

As someone who has navigated the labyrinthine complexities of GitHub Actions, I can tell you that debugging a failing workflow often feels like a descent into madness. You find yourself pushing change after change to a remote repository, racking up action minutes, and crossing your fingers each time. Let me share with you a dramatized but all-too-real sequence of git commit messages you might find yourself typing.

```shell
git commit -m "fix: initial attempt to debug this maze of a workflow"
git commit -m "fix: YAML more like WhyML, am I right?"
git commit -m "fix: removed that pesky tab, should be spaced now, or so I pray"
git commit -m "fix: reverted because the improvement was a trainwreck"
git commit -m "fix: action minutes are the new Bitcoin, and I'm broke"
git commit -m "fix: if this doesn’t work, I’m becoming a goat farmer"
```