# Go Concurrency

Patterns for goroutines, channels, sync primitives, context, errgroup, and worker pools.

---

## Worker Pool Pattern

A fixed number of goroutines process work from a shared channel. This bounds resource usage and provides natural backpressure.

```go
func ProcessItems(ctx context.Context, items []Item, workers int) ([]Result, error) {
    jobs := make(chan Item, len(items))
    results := make(chan Result, len(items))
    errs := make(chan error, 1)

    // Start workers.
    var wg sync.WaitGroup
    for i := 0; i < workers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for item := range jobs {
                result, err := process(ctx, item)
                if err != nil {
                    // Non-blocking send — only first error captured.
                    select {
                    case errs <- err:
                    default:
                    }
                    return
                }
                results <- result
            }
        }()
    }

    // Enqueue work.
    for _, item := range items {
        jobs <- item
    }
    close(jobs)

    // Wait for all workers, then close results.
    wg.Wait()
    close(results)
    close(errs)

    // Check for errors.
    if err := <-errs; err != nil {
        return nil, fmt.Errorf("process items: %w", err)
    }

    // Collect results.
    out := make([]Result, 0, len(items))
    for r := range results {
        out = append(out, r)
    }

    return out, nil
}
```

---

## Context for Cancellation and Timeouts

Use `context.Context` to propagate deadlines and cancellation signals through the call chain.

### Timeout

```go
func FetchWithTimeout(url string, timeout time.Duration) ([]byte, error) {
    ctx, cancel := context.WithTimeout(context.Background(), timeout)
    defer cancel()

    req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
    if err != nil {
        return nil, fmt.Errorf("create request: %w", err)
    }

    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        return nil, fmt.Errorf("fetch %s: %w", url, err)
    }
    defer resp.Body.Close()

    body, err := io.ReadAll(resp.Body)
    if err != nil {
        return nil, fmt.Errorf("read response body: %w", err)
    }

    return body, nil
}
```

### Cancellation

```go
func LongRunningTask(ctx context.Context) error {
    for i := 0; i < 1000; i++ {
        select {
        case <-ctx.Done():
            return ctx.Err()
        default:
        }

        if err := doStep(i); err != nil {
            return fmt.Errorf("step %d: %w", i, err)
        }
    }
    return nil
}
```

---

## Graceful Shutdown

Capture OS signals and drain in-flight work before exiting.

```go
func main() {
    srv := &http.Server{
        Addr:         ":8080",
        Handler:      newRouter(),
        ReadTimeout:  5 * time.Second,
        WriteTimeout: 10 * time.Second,
        IdleTimeout:  120 * time.Second,
    }

    // Start server in a goroutine.
    go func() {
        if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
            log.Fatalf("listen: %v", err)
        }
    }()

    // Wait for interrupt signal.
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit
    log.Println("shutting down server...")

    // Give in-flight requests 30 seconds to complete.
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    if err := srv.Shutdown(ctx); err != nil {
        log.Fatalf("server forced shutdown: %v", err)
    }

    log.Println("server exited cleanly")
}
```

---

## errgroup for Coordinated Goroutines

`errgroup.Group` manages a set of goroutines and returns the first error. Combined with `WithContext`, cancellation propagates automatically to all goroutines when one fails.

```go
func FetchAll(ctx context.Context, urls []string) (map[string][]byte, error) {
    g, ctx := errgroup.WithContext(ctx)

    var mu sync.Mutex
    results := make(map[string][]byte, len(urls))

    for _, url := range urls {
        g.Go(func() error {
            body, err := FetchWithTimeout(url, 10*time.Second)
            if err != nil {
                return fmt.Errorf("fetch %s: %w", url, err)
            }

            mu.Lock()
            results[url] = body
            mu.Unlock()

            return nil
        })
    }

    if err := g.Wait(); err != nil {
        return nil, err
    }

    return results, nil
}
```

### errgroup with Concurrency Limit

```go
func ProcessAll(ctx context.Context, items []Item) error {
    g, ctx := errgroup.WithContext(ctx)
    g.SetLimit(10) // at most 10 concurrent goroutines

    for _, item := range items {
        g.Go(func() error {
            return processItem(ctx, item)
        })
    }

    return g.Wait()
}
```

---

## Avoiding Goroutine Leaks

Every goroutine you start must have a clear exit path. Leaked goroutines consume memory and CPU forever.

### Buffered Channel for Fire-and-Forget

If the receiver might not read, use a buffered channel so the sender never blocks.

```go
func StartTask(ctx context.Context) <-chan Result {
    ch := make(chan Result, 1) // buffer of 1 so sender never blocks

    go func() {
        defer close(ch)
        result, err := doWork(ctx)
        if err != nil {
            ch <- Result{Err: err}
            return
        }
        ch <- Result{Value: result}
    }()

    return ch
}
```

### Select with ctx.Done

Always include a `ctx.Done()` case in select statements inside goroutines so they terminate when the context is cancelled.

```go
func Produce(ctx context.Context, ch chan<- int) {
    defer close(ch)

    for i := 0; ; i++ {
        select {
        case <-ctx.Done():
            return // context cancelled — exit cleanly
        case ch <- i:
        }
    }
}
```

### Prevent Ticker Leak

```go
func PollStatus(ctx context.Context, interval time.Duration) error {
    ticker := time.NewTicker(interval)
    defer ticker.Stop() // always stop the ticker

    for {
        select {
        case <-ctx.Done():
            return ctx.Err()
        case <-ticker.C:
            if err := checkStatus(); err != nil {
                return fmt.Errorf("status check: %w", err)
            }
        }
    }
}
```

---

## sync Primitives Quick Reference

| Primitive | Use when... |
|-----------|-------------|
| `sync.Mutex` | Protecting shared state from concurrent access |
| `sync.RWMutex` | Many readers, few writers |
| `sync.Once` | One-time initialization (lazy singletons) |
| `sync.WaitGroup` | Waiting for a set of goroutines to finish |
| `sync.Map` | Highly concurrent map with few writes (otherwise use Mutex + map) |
| `sync.Pool` | Reusing temporary objects to reduce GC pressure |
| `atomic.*` | Lock-free counters and flags |

### sync.Once Example

```go
type DBPool struct {
    once sync.Once
    pool *sql.DB
}

func (d *DBPool) Get(dsn string) (*sql.DB, error) {
    var err error
    d.once.Do(func() {
        d.pool, err = sql.Open("postgres", dsn)
    })
    if err != nil {
        return nil, fmt.Errorf("open database: %w", err)
    }
    return d.pool, nil
}
```
