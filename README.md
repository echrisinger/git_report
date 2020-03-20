Dependencies:

Install fswatch.
```
brew install fswatch
```

Listen on a file:
`fswatch -0 -t --format-time '%F %T %z' README.md | xargs -0 -n 1 -I{} python git_report/display_logs.py '{}'`
.
