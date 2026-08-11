# Go Patterns & Idioms

Idiomatic Go patterns for error handling, interfaces, package organization, struct design, and functional options.

---

## Error Handling

### Wrap Errors with Context

Always add context when propagating errors so the call chain is visible in logs.

```go
func LoadConfig(path string) (*Config, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return nil, fmt.Errorf("load config %s: %w", path, err)
    }

    var cfg Config
    if err := json.Unmarshal(data, &cfg); err != nil {
        return nil, fmt.Errorf("parse config %s: %w", path, err)
    }

    return &cfg, nil
}
```

### Custom Error Types

Use custom error types when callers need to inspect error details programmatically.

```go
// ValidationError carries field-level detail for API responses.
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation: field %s: %s", e.Field, e.Message)
}

// Sentinel errors for well-known conditions.
var (
    ErrNotFound      = errors.New("not found")
    ErrAlreadyExists = errors.New("already exists")
    ErrUnauthorized  = errors.New("unauthorized")
)
```

### errors.Is and errors.As

Use `errors.Is` to check for sentinel errors and `errors.As` to extract custom error types, even through wrapped chains.

```go
func HandleError(err error) {
    // Check sentinel
    if errors.Is(err, ErrNotFound) {
        log.Println("resource not found")
        return
    }

    // Extract custom type
    var valErr *ValidationError
    if errors.As(err, &valErr) {
        log.Printf("invalid field %s: %s", valErr.Field, valErr.Message)
        return
    }

    log.Printf("unexpected error: %v", err)
}
```

### Never Ignore Errors

```go
// WRONG: silently discards the error
data, _ := json.Marshal(payload)

// CORRECT: handle or propagate every error
data, err := json.Marshal(payload)
if err != nil {
    return fmt.Errorf("marshal payload: %w", err)
}
```

---

## Interfaces

### Small, Focused Interfaces

Prefer single-method interfaces; compose them when needed.

```go
// Single-method interfaces — easy to implement and mock.
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

// Compose when a function needs both capabilities.
type ReadWriter interface {
    Reader
    Writer
}
```

### Define Interfaces Where They Are Used

The consumer defines the interface, not the provider. This keeps packages decoupled.

```go
// package order — the consumer defines what it needs.
package order

// PaymentProcessor is the interface this package depends on.
type PaymentProcessor interface {
    Charge(ctx context.Context, amount int64, currency string) (string, error)
}

type Service struct {
    payments PaymentProcessor
}

func NewService(p PaymentProcessor) *Service {
    return &Service{payments: p}
}
```

```go
// package stripe — the provider just implements methods.
package stripe

type Client struct {
    apiKey string
}

func (c *Client) Charge(ctx context.Context, amount int64, currency string) (string, error) {
    // Stripe-specific implementation
    return "ch_123", nil
}
```

### Optional Behavior with Type Assertions

Check for optional interfaces at runtime to enable advanced capabilities without requiring them.

```go
type Flusher interface {
    Flush() error
}

func WriteData(w io.Writer, data []byte) error {
    if _, err := w.Write(data); err != nil {
        return fmt.Errorf("write: %w", err)
    }

    // Flush if the writer supports it.
    if f, ok := w.(Flusher); ok {
        if err := f.Flush(); err != nil {
            return fmt.Errorf("flush: %w", err)
        }
    }

    return nil
}
```

---

## Package Organization

### Standard Project Layout

```
project/
  cmd/
    server/         # main.go for the HTTP server binary
    cli/            # main.go for a CLI tool
  internal/
    user/           # business logic — not importable outside this module
    order/
    storage/
  pkg/
    httputil/       # reusable library code safe for external import
    validator/
  api/
    openapi.yaml    # API specifications
  migrations/       # database migration files
  go.mod
  go.sum
```

- `cmd/` — each subdirectory is a separate binary with its own `main.go`.
- `internal/` — enforced by the Go toolchain; code here cannot be imported by other modules.
- `pkg/` — reusable libraries intended for external consumption.
- `api/` — API contracts (OpenAPI, protobuf, GraphQL schemas).

### Package Naming Conventions

```go
// GOOD: short, lowercase, single-word names
package user
package http
package auth

// BAD: stuttering, generic, or utility-dump names
package userService   // stutters with user.Service
package utils         // grab-bag with no cohesion
package common        // same problem as utils
package helpers       // same problem as utils
```

### Avoid Package-Level State

Package-level variables create hidden coupling, make testing harder, and break concurrency safety. Use dependency injection instead.

```go
// WRONG: package-level mutable state
var db *sql.DB

func GetUser(id string) (*User, error) {
    return queryUser(db, id)
}

// CORRECT: inject dependencies
type UserStore struct {
    db *sql.DB
}

func NewUserStore(db *sql.DB) *UserStore {
    return &UserStore{db: db}
}

func (s *UserStore) GetUser(ctx context.Context, id string) (*User, error) {
    row := s.db.QueryRowContext(ctx, "SELECT id, name FROM users WHERE id = $1", id)
    var u User
    if err := row.Scan(&u.ID, &u.Name); err != nil {
        return nil, fmt.Errorf("get user %s: %w", id, err)
    }
    return &u, nil
}
```

---

## Struct Design

### Functional Options Pattern

Use functional options for constructors with many optional parameters. This keeps the API clean, extensible, and backward-compatible.

```go
type Server struct {
    addr         string
    port         int
    readTimeout  time.Duration
    writeTimeout time.Duration
    maxConns     int
    logger       *slog.Logger
}

type Option func(*Server)

func WithPort(port int) Option {
    return func(s *Server) {
        s.port = port
    }
}

func WithReadTimeout(d time.Duration) Option {
    return func(s *Server) {
        s.readTimeout = d
    }
}

func WithWriteTimeout(d time.Duration) Option {
    return func(s *Server) {
        s.writeTimeout = d
    }
}

func WithMaxConns(n int) Option {
    return func(s *Server) {
        s.maxConns = n
    }
}

func WithLogger(l *slog.Logger) Option {
    return func(s *Server) {
        s.logger = l
    }
}

func NewServer(addr string, opts ...Option) *Server {
    s := &Server{
        addr:         addr,
        port:         8080,
        readTimeout:  5 * time.Second,
        writeTimeout: 10 * time.Second,
        maxConns:     100,
        logger:       slog.Default(),
    }
    for _, opt := range opts {
        opt(s)
    }
    return s
}

// Usage:
// srv := NewServer("0.0.0.0",
//     WithPort(9090),
//     WithReadTimeout(10*time.Second),
//     WithLogger(customLogger),
// )
```

### Embedding for Composition

Prefer composition (embedding) over inheritance. Embed types to reuse behavior without deep hierarchies.

```go
type Timestamped struct {
    CreatedAt time.Time
    UpdatedAt time.Time
}

type User struct {
    Timestamped
    ID    string
    Name  string
    Email string
}

// The User type promotes Timestamped fields:
// u := User{}
// u.CreatedAt = time.Now()  // direct access
```

---

## Anti-Patterns

### Naked Returns

Naked returns obscure what is being returned. Always name your return values only for documentation; use explicit returns.

```go
// BAD: naked return hides what is returned
func divide(a, b float64) (result float64, err error) {
    if b == 0 {
        err = errors.New("division by zero")
        return // what is result here?
    }
    result = a / b
    return
}

// GOOD: explicit returns
func divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, errors.New("division by zero")
    }
    return a / b, nil
}
```

### Panic for Control Flow

```go
// BAD: panic as control flow
func MustParse(s string) int {
    v, err := strconv.Atoi(s)
    if err != nil {
        panic(err) // crashes the program
    }
    return v
}

// GOOD: return error and let the caller decide
func Parse(s string) (int, error) {
    v, err := strconv.Atoi(s)
    if err != nil {
        return 0, fmt.Errorf("parse int %q: %w", s, err)
    }
    return v, nil
}
```

### Context in Struct

```go
// BAD: storing context in a struct
type Worker struct {
    ctx context.Context // context outlives the request
    db  *sql.DB
}

// GOOD: pass context as first function parameter
type Worker struct {
    db *sql.DB
}

func (w *Worker) Process(ctx context.Context, id string) error {
    return w.db.QueryRowContext(ctx, "SELECT 1 FROM jobs WHERE id = $1", id).Err()
}
```

### Mixed Receiver Types

```go
// BAD: mixing value and pointer receivers on the same type
func (u User) Name() string   { return u.name }
func (u *User) SetName(n string) { u.name = n }

// GOOD: pick one receiver type and be consistent
func (u *User) Name() string      { return u.name }
func (u *User) SetName(n string)  { u.name = n }
```
