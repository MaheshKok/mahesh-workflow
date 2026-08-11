# Go Testing

TDD workflow, table-driven tests, subtests, benchmarks, fuzzing, mocking, and HTTP handler testing patterns.

---

## TDD Workflow

Red-Green-Refactor:

1. **RED** — Write a test for the next piece of behavior. Run it. It must fail.
2. **GREEN** — Write the minimum implementation to make the test pass.
3. **REFACTOR** — Clean up the code while keeping tests green.

```go
// Step 1: RED — write the test first (calculator_test.go)
func TestAdd(t *testing.T) {
    got := calculator.Add(2, 3)
    want := 5
    if got != want {
        t.Errorf("Add(2, 3) = %d, want %d", got, want)
    }
}

// Step 2: GREEN — minimal implementation (calculator.go)
func Add(a, b int) int {
    return a + b
}

// Step 3: REFACTOR — nothing to simplify here, move to next test
```

---

## Table-Driven Tests

The default test pattern in Go. Each row is an independent test case.

### Basic Table-Driven Test

```go
func TestParseSize(t *testing.T) {
    tests := []struct {
        name  string
        input string
        want  int64
    }{
        {name: "bytes", input: "100B", want: 100},
        {name: "kilobytes", input: "2KB", want: 2048},
        {name: "megabytes", input: "1MB", want: 1048576},
        {name: "gigabytes", input: "1GB", want: 1073741824},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := ParseSize(tt.input)
            if err != nil {
                t.Fatalf("ParseSize(%q) returned unexpected error: %v", tt.input, err)
            }
            if got != tt.want {
                t.Errorf("ParseSize(%q) = %d, want %d", tt.input, got, tt.want)
            }
        })
    }
}
```

### Table-Driven Test with Error Cases

```go
func TestParseSize_Errors(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        wantErr string
    }{
        {name: "empty string", input: "", wantErr: "empty input"},
        {name: "no unit", input: "100", wantErr: "missing unit"},
        {name: "invalid unit", input: "100XB", wantErr: "unknown unit"},
        {name: "negative value", input: "-5KB", wantErr: "negative size"},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            _, err := ParseSize(tt.input)
            if err == nil {
                t.Fatalf("ParseSize(%q) expected error containing %q, got nil", tt.input, tt.wantErr)
            }
            if !strings.Contains(err.Error(), tt.wantErr) {
                t.Errorf("ParseSize(%q) error = %q, want substring %q", tt.input, err.Error(), tt.wantErr)
            }
        })
    }
}
```

---

## Subtests and Parallel Subtests

### Grouping Related Tests

```go
func TestUserService(t *testing.T) {
    t.Run("Create", func(t *testing.T) {
        t.Run("valid user", func(t *testing.T) {
            // ...
        })
        t.Run("duplicate email", func(t *testing.T) {
            // ...
        })
    })

    t.Run("Delete", func(t *testing.T) {
        t.Run("existing user", func(t *testing.T) {
            // ...
        })
        t.Run("nonexistent user", func(t *testing.T) {
            // ...
        })
    })
}
```

### Parallel Subtests

```go
func TestFetchURLs(t *testing.T) {
    urls := []string{
        "https://example.com/a",
        "https://example.com/b",
        "https://example.com/c",
    }

    for _, url := range urls {
        t.Run(url, func(t *testing.T) {
            t.Parallel() // runs this subtest concurrently with others

            resp, err := http.Get(url)
            if err != nil {
                t.Fatalf("GET %s: %v", url, err)
            }
            defer resp.Body.Close()

            if resp.StatusCode != http.StatusOK {
                t.Errorf("GET %s status = %d, want 200", url, resp.StatusCode)
            }
        })
    }
}
```

---

## Test Helpers

### t.Helper

Mark functions as test helpers so failure messages point to the caller, not the helper.

```go
func assertEqual[T comparable](t *testing.T, got, want T) {
    t.Helper()
    if got != want {
        t.Errorf("got %v, want %v", got, want)
    }
}

func assertNoError(t *testing.T, err error) {
    t.Helper()
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
}
```

### t.Cleanup

Register cleanup functions that run after the test completes, even on failure.

```go
func setupTestDB(t *testing.T) *sql.DB {
    t.Helper()

    db, err := sql.Open("sqlite3", ":memory:")
    if err != nil {
        t.Fatalf("open test db: %v", err)
    }

    t.Cleanup(func() {
        db.Close()
    })

    return db
}
```

### t.TempDir

Automatically creates and cleans up a temporary directory.

```go
func TestWriteFile(t *testing.T) {
    dir := t.TempDir() // cleaned up automatically

    path := filepath.Join(dir, "output.txt")
    err := WriteFile(path, []byte("hello"))
    assertNoError(t, err)

    got, err := os.ReadFile(path)
    assertNoError(t, err)
    assertEqual(t, string(got), "hello")
}
```

---

## Golden Files

Compare output against a known-good reference file. Use `-update` flag to regenerate.

```go
var update = flag.Bool("update", false, "update golden files")

func TestRenderTemplate(t *testing.T) {
    got := RenderTemplate(testData)

    goldenPath := filepath.Join("testdata", t.Name()+".golden")

    if *update {
        err := os.WriteFile(goldenPath, []byte(got), 0o644)
        if err != nil {
            t.Fatalf("update golden file: %v", err)
        }
        return
    }

    want, err := os.ReadFile(goldenPath)
    if err != nil {
        t.Fatalf("read golden file: %v", err)
    }

    if got != string(want) {
        t.Errorf("output mismatch (-want +got):\n%s", diff(string(want), got))
    }
}
```

---

## Interface-Based Mocking

Define mocks using function fields that match the interface. No external mocking library needed.

```go
// The interface (defined where it's used).
type UserRepository interface {
    GetByID(ctx context.Context, id string) (*User, error)
    Save(ctx context.Context, user *User) error
}

// Mock with function fields.
type MockUserRepository struct {
    GetByIDFunc func(ctx context.Context, id string) (*User, error)
    SaveFunc    func(ctx context.Context, user *User) error
}

func (m *MockUserRepository) GetByID(ctx context.Context, id string) (*User, error) {
    return m.GetByIDFunc(ctx, id)
}

func (m *MockUserRepository) Save(ctx context.Context, user *User) error {
    return m.SaveFunc(ctx, user)
}

// Usage in tests:
func TestCreateUser(t *testing.T) {
    var savedUser *User

    repo := &MockUserRepository{
        GetByIDFunc: func(_ context.Context, id string) (*User, error) {
            return nil, ErrNotFound
        },
        SaveFunc: func(_ context.Context, user *User) error {
            savedUser = user
            return nil
        },
    }

    svc := NewUserService(repo)
    err := svc.Create(context.Background(), "alice", "alice@example.com")
    assertNoError(t, err)

    if savedUser == nil {
        t.Fatal("expected user to be saved")
    }
    assertEqual(t, savedUser.Name, "alice")
    assertEqual(t, savedUser.Email, "alice@example.com")
}
```

---

## Benchmarks

### Basic Benchmark

```go
func BenchmarkFibonacci(b *testing.B) {
    for b.Loop() {
        Fibonacci(20)
    }
}
```

### Benchmark with Different Sizes

```go
func BenchmarkSort(b *testing.B) {
    sizes := []int{100, 1000, 10000}

    for _, size := range sizes {
        b.Run(fmt.Sprintf("size=%d", size), func(b *testing.B) {
            data := generateSlice(size)
            b.ResetTimer()

            for b.Loop() {
                sorted := make([]int, len(data))
                copy(sorted, data)
                sort.Ints(sorted)
            }
        })
    }
}
```

### Memory Allocation Benchmark

```go
func BenchmarkStringConcat(b *testing.B) {
    b.Run("plus_operator", func(b *testing.B) {
        b.ReportAllocs()
        for b.Loop() {
            s := ""
            for i := 0; i < 100; i++ {
                s += "x"
            }
        }
    })

    b.Run("strings_builder", func(b *testing.B) {
        b.ReportAllocs()
        for b.Loop() {
            var sb strings.Builder
            for i := 0; i < 100; i++ {
                sb.WriteString("x")
            }
            _ = sb.String()
        }
    })
}
```

---

## Fuzzing

### Basic Fuzz Test

```go
func FuzzParseSize(f *testing.F) {
    // Seed corpus — known inputs to start from.
    f.Add("100B")
    f.Add("2KB")
    f.Add("1MB")
    f.Add("")

    f.Fuzz(func(t *testing.T, input string) {
        result, err := ParseSize(input)
        if err != nil {
            return // invalid input is fine
        }
        if result < 0 {
            t.Errorf("ParseSize(%q) = %d, want non-negative", input, result)
        }
    })
}
```

### Multi-Input Fuzz Test

```go
func FuzzJSONRoundtrip(f *testing.F) {
    f.Add("alice", 30, true)

    f.Fuzz(func(t *testing.T, name string, age int, active bool) {
        u := User{Name: name, Age: age, Active: active}

        data, err := json.Marshal(u)
        if err != nil {
            t.Fatalf("marshal: %v", err)
        }

        var decoded User
        if err := json.Unmarshal(data, &decoded); err != nil {
            t.Fatalf("unmarshal: %v", err)
        }

        if decoded != u {
            t.Errorf("roundtrip mismatch: got %+v, want %+v", decoded, u)
        }
    })
}
```

---

## Test Coverage

```bash
# Run tests with coverage
go test -cover ./...

# Generate coverage profile
go test -coverprofile=coverage.out ./...

# View in browser
go tool cover -html=coverage.out

# Check coverage percentage
go tool cover -func=coverage.out | tail -1
```

**Targets:**
- Minimum: 80% overall
- Critical paths (auth, payments, data mutations): 90%+

---

## HTTP Handler Testing

Use `httptest` to test handlers without starting a real server.

```go
func TestHealthHandler(t *testing.T) {
    req := httptest.NewRequest(http.MethodGet, "/health", nil)
    rec := httptest.NewRecorder()

    HealthHandler(rec, req)

    if rec.Code != http.StatusOK {
        t.Errorf("status = %d, want %d", rec.Code, http.StatusOK)
    }

    var body map[string]string
    if err := json.NewDecoder(rec.Body).Decode(&body); err != nil {
        t.Fatalf("decode response: %v", err)
    }

    assertEqual(t, body["status"], "ok")
}

func TestCreateUserHandler(t *testing.T) {
    payload := `{"name": "alice", "email": "alice@example.com"}`
    req := httptest.NewRequest(http.MethodPost, "/users", strings.NewReader(payload))
    req.Header.Set("Content-Type", "application/json")
    rec := httptest.NewRecorder()

    repo := &MockUserRepository{
        SaveFunc: func(_ context.Context, user *User) error {
            return nil
        },
    }
    handler := NewUserHandler(repo)
    handler.Create(rec, req)

    if rec.Code != http.StatusCreated {
        t.Errorf("status = %d, want %d", rec.Code, http.StatusCreated)
    }
}
```

---

## Best Practices

### DO

- Use `t.Helper()` in all test helper functions.
- Use `t.Parallel()` for independent tests to speed up the suite.
- Use `t.Cleanup()` instead of `defer` for resource teardown.
- Use `t.TempDir()` instead of manual temp directories.
- Put test fixtures in `testdata/` (ignored by `go build`).
- Test behavior, not implementation.
- Use `errors.Is` / `errors.As` to check errors in tests.
- Run `go test -race ./...` in CI.

### DON'T

- Don't use `assert` libraries — the standard library is sufficient.
- Don't test private functions directly — test through the public API.
- Don't use `init()` in test files.
- Don't rely on test execution order.
- Don't put test logic in `TestMain` unless necessary (setup/teardown for the entire package).
- Don't use `time.Sleep` in tests — use channels, contexts, or polling helpers.

---

## CI/CD: GitHub Actions Example

```yaml
name: Go CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.23'

      - name: Test
        run: go test -race -coverprofile=coverage.out ./...

      - name: Check coverage
        run: |
          COVERAGE=$(go tool cover -func=coverage.out | tail -1 | awk '{print $3}' | tr -d '%')
          echo "Coverage: ${COVERAGE}%"
          if (( $(echo "$COVERAGE < 80" | bc -l) )); then
            echo "Coverage below 80%"
            exit 1
          fi

      - name: Vet
        run: go vet ./...

      - name: Staticcheck
        uses: dominikh/staticcheck-action@v1
```
