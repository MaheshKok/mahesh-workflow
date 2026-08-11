# Go Performance

Memory optimization, sync.Pool, string building, essential tooling, linter configuration, and idioms quick reference.

---

## Memory Optimization

### Preallocate Slices

When the output size is known or estimable, preallocate to avoid repeated resizing.

```go
// BAD: grows the slice incrementally, causing multiple allocations
func Transform(items []Item) []Result {
    var results []Result
    for _, item := range items {
        results = append(results, convert(item))
    }
    return results
}

// GOOD: single allocation
func Transform(items []Item) []Result {
    results := make([]Result, 0, len(items))
    for _, item := range items {
        results = append(results, convert(item))
    }
    return results
}
```

### Preallocate Maps

```go
// BAD: map grows and rehashes as entries are added
m := make(map[string]int)

// GOOD: hint at expected size
m := make(map[string]int, len(keys))
```

### Avoid Slice Memory Leaks

Large backing arrays can be retained by small slices. Copy when returning a subset.

```go
// BAD: retains the entire backing array
func FirstN(data []byte, n int) []byte {
    return data[:n]
}

// GOOD: copies to a new, right-sized slice
func FirstN(data []byte, n int) []byte {
    result := make([]byte, n)
    copy(result, data[:n])
    return result
}
```

---

## sync.Pool

Reuse frequently allocated temporary objects to reduce GC pressure. Good for buffers, encoders, and similar short-lived objects.

```go
var bufPool = sync.Pool{
    New: func() any {
        return new(bytes.Buffer)
    },
}

func FormatRecord(r Record) (string, error) {
    buf := bufPool.Get().(*bytes.Buffer)
    defer func() {
        buf.Reset()
        bufPool.Put(buf)
    }()

    if err := r.WriteTo(buf); err != nil {
        return "", fmt.Errorf("format record: %w", err)
    }

    return buf.String(), nil
}
```

### When to use sync.Pool

| Scenario | Use sync.Pool? |
|----------|---------------|
| High-frequency allocations in hot paths | Yes |
| Buffers reused across HTTP requests | Yes |
| Long-lived objects | No |
| Objects with complex initialization | No — use sync.Once |
| Objects shared across goroutines simultaneously | No — Pool items are per-goroutine |

---

## String Building

### strings.Builder vs Concatenation

```go
// BAD: O(n^2) — creates a new string on every iteration
func JoinSlow(words []string) string {
    result := ""
    for _, w := range words {
        result += w + " "
    }
    return result
}

// GOOD: O(n) — writes to an internal buffer
func JoinFast(words []string) string {
    var sb strings.Builder
    sb.Grow(estimateSize(words)) // optional: preallocate buffer

    for i, w := range words {
        if i > 0 {
            sb.WriteByte(' ')
        }
        sb.WriteString(w)
    }

    return sb.String()
}

// BEST for simple joins — use the standard library
func JoinBest(words []string) string {
    return strings.Join(words, " ")
}
```

### fmt.Fprintf to a Builder

```go
func BuildReport(items []LineItem) string {
    var sb strings.Builder
    sb.WriteString("Report\n")
    sb.WriteString("------\n")

    var total float64
    for _, item := range items {
        fmt.Fprintf(&sb, "%-20s $%.2f\n", item.Name, item.Price)
        total += item.Price
    }

    fmt.Fprintf(&sb, "\nTotal: $%.2f\n", total)
    return sb.String()
}
```

---

## Essential Go Tooling

| Command | Purpose |
|---------|---------|
| `go build ./...` | Compile all packages (catches type errors) |
| `go test -race -cover ./...` | Run tests with race detector and coverage |
| `go test -bench=. -benchmem ./...` | Run benchmarks with memory allocation stats |
| `go vet ./...` | Report likely bugs (printf args, unreachable code, etc.) |
| `go mod tidy` | Remove unused and add missing module dependencies |
| `go mod verify` | Verify downloaded modules match expected hashes |
| `staticcheck ./...` | Advanced static analysis (supplements go vet) |
| `golangci-lint run` | Meta-linter that runs many linters in parallel |
| `gofmt -s -w .` | Format and simplify code |
| `goimports -w .` | Format code and fix import grouping |
| `go tool pprof` | CPU and memory profiling |
| `go tool trace` | Execution tracing for concurrency analysis |

---

## Recommended .golangci.yml

```yaml
run:
  timeout: 5m

linters:
  enable:
    - errcheck        # check that errors are handled
    - govet           # reports suspicious constructs
    - staticcheck     # advanced static analysis
    - unused          # detect unused code
    - gosimple        # simplify code
    - ineffassign     # detect ineffectual assignments
    - typecheck       # type-check code
    - gocritic        # opinionated style and performance checks
    - revive          # configurable replacement for golint
    - misspell        # catch common misspellings
    - prealloc        # suggest preallocations
    - unconvert       # remove unnecessary type conversions
    - unparam         # detect unused function parameters
    - errname         # check error variable naming (errFoo)
    - exhaustive      # check exhaustive switch on enums
    - noctx           # detect http requests without context
    - bodyclose       # detect unclosed HTTP response bodies
    - gosec           # security-oriented checks

linters-settings:
  gocritic:
    enabled-tags:
      - diagnostic
      - style
      - performance
    disabled-checks:
      - ifElseChain    # too noisy for table-driven code

  revive:
    rules:
      - name: exported
        arguments:
          - checkPrivateReceivers
      - name: blank-imports
      - name: context-as-argument
      - name: dot-imports
      - name: error-return
      - name: error-strings
      - name: error-naming
      - name: increment-decrement
      - name: var-naming
      - name: range
      - name: receiver-naming
      - name: time-naming
      - name: unexported-return
      - name: indent-error-flow
      - name: errorf
      - name: empty-block
      - name: superfluous-else
      - name: unreachable-code

  gosec:
    excludes:
      - G104  # allow unhandled errors in defer
    severity: medium

  errcheck:
    check-type-assertions: true
    check-blank: true

issues:
  max-issues-per-linter: 50
  max-same-issues: 5

  exclude-rules:
    - path: _test\.go
      linters:
        - gosec
        - errcheck
```

---

## Go Idioms Quick Reference

| Idiom | Example |
|-------|---------|
| Zero value is useful | `var buf bytes.Buffer` — ready to use without initialization |
| Comma-ok pattern | `val, ok := myMap[key]` |
| Type assertion | `s, ok := i.(string)` |
| Type switch | `switch v := i.(type) { case string: ... }` |
| Blank identifier | `for _, v := range items` — discard index |
| Defer for cleanup | `f, _ := os.Open(p); defer f.Close()` |
| Init with composite literal | `p := &Point{X: 1, Y: 2}` |
| Named return for docs only | `func (f *File) Read(b []byte) (n int, err error)` |
| Stringer interface | `func (s Status) String() string` |
| Enums with iota | `const ( A Kind = iota; B; C )` |
| Sentinel errors | `var ErrNotFound = errors.New("not found")` |
| Table-driven tests | `for _, tt := range tests { t.Run(...) }` |
| Goroutine + channel | `go func() { ch <- result }()` |
| Select for multiplexing | `select { case v := <-ch: ... case <-ctx.Done(): ... }` |
| Functional options | `NewServer(addr, WithPort(8080))` |
| Embed for composition | `type Server struct { http.Handler }` |
