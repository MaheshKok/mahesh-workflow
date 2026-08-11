# Performance

## Memoization

### useMemo — cache expensive computations

Only use when the computation is genuinely expensive. Do not memoize trivial operations.

```tsx
import { useMemo } from 'react';

interface OrderSummaryProps {
  readonly orders: readonly Order[];
  readonly filterStatus: OrderStatus;
}

function OrderSummary({ orders, filterStatus }: OrderSummaryProps): React.JSX.Element {
  // Expensive: filtering + aggregation on potentially large array
  const summary = useMemo(() => {
    const filtered = orders.filter((order) => order.status === filterStatus);
    const totalRevenue = filtered.reduce((sum, order) => sum + order.total, 0);
    const averageOrderValue = filtered.length > 0 ? totalRevenue / filtered.length : 0;

    return {
      count: filtered.length,
      totalRevenue,
      averageOrderValue,
      orders: filtered,
    };
  }, [orders, filterStatus]);

  return (
    <div>
      <p>Orders: {summary.count}</p>
      <p>Revenue: ${summary.totalRevenue.toFixed(2)}</p>
      <p>AOV: ${summary.averageOrderValue.toFixed(2)}</p>
      <OrderTable orders={summary.orders} />
    </div>
  );
}
```

### useCallback — stabilize function references

Prevents child re-renders when the function identity would otherwise change every render.

```tsx
import { useCallback, useState } from 'react';

function TodoApp(): React.JSX.Element {
  const [todos, setTodos] = useState<readonly Todo[]>([]);

  // Stable reference — only changes if setTodos changes (it won't)
  const addTodo = useCallback((text: string) => {
    setTodos((prev) => [
      ...prev,
      { id: crypto.randomUUID(), text, completed: false },
    ]);
  }, []);

  const toggleTodo = useCallback((id: string) => {
    setTodos((prev) =>
      prev.map((todo) =>
        todo.id === id ? { ...todo, completed: !todo.completed } : todo,
      ),
    );
  }, []);

  const removeTodo = useCallback((id: string) => {
    setTodos((prev) => prev.filter((todo) => todo.id !== id));
  }, []);

  return (
    <div>
      <AddTodoForm onAdd={addTodo} />
      <TodoList todos={todos} onToggle={toggleTodo} onRemove={removeTodo} />
    </div>
  );
}
```

### React.memo — skip re-renders when props are unchanged

Wrap components that receive stable props but sit below frequently-updating parents.

```tsx
import { memo } from 'react';

interface TodoItemProps {
  readonly todo: Todo;
  readonly onToggle: (id: string) => void;
  readonly onRemove: (id: string) => void;
}

const TodoItem = memo(function TodoItem({
  todo,
  onToggle,
  onRemove,
}: TodoItemProps): React.JSX.Element {
  return (
    <li className={todo.completed ? 'completed' : ''}>
      <label>
        <input
          type="checkbox"
          checked={todo.completed}
          onChange={() => onToggle(todo.id)}
        />
        {todo.text}
      </label>
      <button onClick={() => onRemove(todo.id)}>Delete</button>
    </li>
  );
});

// With custom comparison for complex props
const ExpensiveChart = memo(
  function ExpensiveChart({ data, config }: ChartProps): React.JSX.Element {
    return <canvas ref={renderChart(data, config)} />;
  },
  (prevProps, nextProps) => {
    // Only re-render if data length or config changes
    return (
      prevProps.data.length === nextProps.data.length &&
      prevProps.config.type === nextProps.config.type
    );
  },
);
```

## Code Splitting and Lazy Loading

Split heavy components into separate chunks. Load them on demand with `lazy()` and `Suspense`.

```tsx
import { lazy, Suspense } from 'react';

// Lazy-load heavy components
const AnalyticsDashboard = lazy(() => import('./AnalyticsDashboard'));
const AdminPanel = lazy(() => import('./AdminPanel'));
const ChartEditor = lazy(() => import('./ChartEditor'));

function App(): React.JSX.Element {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route
        path="/analytics"
        element={
          <Suspense fallback={<PageSkeleton />}>
            <AnalyticsDashboard />
          </Suspense>
        }
      />
      <Route
        path="/admin"
        element={
          <Suspense fallback={<PageSkeleton />}>
            <AdminPanel />
          </Suspense>
        }
      />
    </Routes>
  );
}

// Reusable lazy wrapper
interface LazyComponentProps {
  readonly fallback?: React.ReactNode;
  readonly children: React.ReactNode;
}

function LazyBoundary({
  fallback = <Spinner />,
  children,
}: LazyComponentProps): React.JSX.Element {
  return (
    <ErrorBoundary fallback={<p>Failed to load component.</p>}>
      <Suspense fallback={fallback}>{children}</Suspense>
    </ErrorBoundary>
  );
}

// Conditional lazy loading — load only when user interacts
function SettingsPage(): React.JSX.Element {
  const { value: showEditor, setTrue: openEditor } = useToggle(false);

  return (
    <div>
      <h1>Settings</h1>
      <button onClick={openEditor}>Open Advanced Editor</button>
      {showEditor && (
        <LazyBoundary fallback={<EditorSkeleton />}>
          <ChartEditor />
        </LazyBoundary>
      )}
    </div>
  );
}
```

## Virtualization for Long Lists

Render only visible items for lists with hundreds or thousands of rows. Use `@tanstack/react-virtual`.

```tsx
import { useVirtualizer } from '@tanstack/react-virtual';
import { useRef } from 'react';

interface VirtualListProps {
  readonly items: readonly ListItem[];
  readonly estimateItemHeight?: number;
}

function VirtualList({
  items,
  estimateItemHeight = 50,
}: VirtualListProps): React.JSX.Element {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => estimateItemHeight,
    overscan: 5, // render 5 extra items above/below viewport
  });

  return (
    <div
      ref={parentRef}
      style={{ height: '600px', overflow: 'auto' }}
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualRow) => {
          const item = items[virtualRow.index];
          return (
            <div
              key={item.id}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualRow.size}px`,
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              <ListItemRow item={item} />
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Variable-height rows with measured sizes
function VirtualListDynamic({ items }: VirtualListProps): React.JSX.Element {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 60,
    overscan: 3,
  });

  return (
    <div ref={parentRef} style={{ height: '600px', overflow: 'auto' }}>
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualRow) => (
          <div
            key={items[virtualRow.index].id}
            ref={virtualizer.measureElement}
            data-index={virtualRow.index}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              transform: `translateY(${virtualRow.start}px)`,
            }}
          >
            <ExpandableListItem item={items[virtualRow.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Database Query Optimization

When writing API routes or server-side code, select only needed columns and limit result sets.

```typescript
// BAD — fetches all columns, all rows
const users = await db.query('SELECT * FROM users');

// GOOD — select only needed columns with limit
const users = await db.query(
  'SELECT id, name, email FROM users WHERE active = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3',
  [true, pageSize, offset],
);

// Using Prisma — select specific fields
const users = await prisma.user.findMany({
  where: { isActive: true },
  select: {
    id: true,
    name: true,
    email: true,
  },
  orderBy: { createdAt: 'desc' },
  take: pageSize,
  skip: offset,
});

// Using Drizzle — explicit column selection
const users = await db
  .select({
    id: usersTable.id,
    name: usersTable.name,
    email: usersTable.email,
  })
  .from(usersTable)
  .where(eq(usersTable.isActive, true))
  .orderBy(desc(usersTable.createdAt))
  .limit(pageSize)
  .offset(offset);

// Batch related queries with Promise.all instead of N+1
// BAD — N+1 queries
const users = await fetchUsers();
for (const user of users) {
  user.orders = await fetchOrdersForUser(user.id); // N queries
}

// GOOD — batch fetch
const users = await fetchUsers();
const userIds = users.map((u) => u.id);
const allOrders = await fetchOrdersByUserIds(userIds); // 1 query
const ordersByUserId = groupBy(allOrders, 'userId');
const usersWithOrders = users.map((user) => ({
  ...user,
  orders: ordersByUserId[user.id] ?? [],
}));
```
