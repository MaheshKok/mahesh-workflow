# State & Hooks

## Custom Hook Patterns

Extract reusable stateful logic into custom hooks. Name them with `use` prefix. Keep hooks focused on a single concern.

### useToggle

```typescript
import { useState, useCallback } from 'react';

interface UseToggleReturn {
  readonly value: boolean;
  readonly toggle: () => void;
  readonly setTrue: () => void;
  readonly setFalse: () => void;
}

function useToggle(initialValue = false): UseToggleReturn {
  const [value, setValue] = useState(initialValue);

  const toggle = useCallback(() => setValue((prev) => !prev), []);
  const setTrue = useCallback(() => setValue(true), []);
  const setFalse = useCallback(() => setValue(false), []);

  return { value, toggle, setTrue, setFalse };
}

// Usage
function Sidebar(): React.JSX.Element {
  const { value: isOpen, toggle, setFalse: close } = useToggle(false);

  return (
    <>
      <button onClick={toggle}>Menu</button>
      {isOpen && <SidebarPanel onClose={close} />}
    </>
  );
}
```

### useDebounce

```typescript
import { useState, useEffect } from 'react';

function useDebounce<T>(value: T, delayMs: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debouncedValue;
}

// Usage
function SearchInput(): React.JSX.Element {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 300);

  useEffect(() => {
    if (debouncedQuery) {
      searchApi(debouncedQuery);
    }
  }, [debouncedQuery]);

  return <input value={query} onChange={(e) => setQuery(e.target.value)} />;
}
```

### useLocalStorage

```typescript
import { useState, useCallback } from 'react';

function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T | ((prev: T) => T)) => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item !== null ? JSON.parse(item) : initialValue;
    } catch {
      console.warn(`Failed to read localStorage key "${key}"`);
      return initialValue;
    }
  });

  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      setStoredValue((prev) => {
        const nextValue = value instanceof Function ? value(prev) : value;
        try {
          window.localStorage.setItem(key, JSON.stringify(nextValue));
        } catch {
          console.warn(`Failed to write localStorage key "${key}"`);
        }
        return nextValue;
      });
    },
    [key],
  );

  return [storedValue, setValue];
}

// Usage
function ThemeToggle(): React.JSX.Element {
  const [theme, setTheme] = useLocalStorage<'light' | 'dark'>('theme', 'light');

  return (
    <button onClick={() => setTheme((prev) => (prev === 'light' ? 'dark' : 'light'))}>
      Current: {theme}
    </button>
  );
}
```

## State Management with useState

Use functional updates when new state depends on previous state. Keep state minimal — derive values instead of storing them.

```typescript
// BAD — storing derived state
const [items, setItems] = useState<Item[]>([]);
const [itemCount, setItemCount] = useState(0); // derived from items.length
const [totalPrice, setTotalPrice] = useState(0); // derived from items

// GOOD — derive from source of truth
const [items, setItems] = useState<Item[]>([]);
const itemCount = items.length;
const totalPrice = items.reduce((sum, item) => sum + item.price, 0);

// GOOD — functional update when new state depends on previous state
function addItem(newItem: Item): void {
  setItems((prev) => [...prev, newItem]);
}

function removeItem(itemId: string): void {
  setItems((prev) => prev.filter((item) => item.id !== itemId));
}

function updateItemQuantity(itemId: string, quantity: number): void {
  setItems((prev) =>
    prev.map((item) =>
      item.id === itemId ? { ...item, quantity } : item,
    ),
  );
}
```

## Context + Reducer Pattern

Use `useReducer` for complex state with multiple sub-values or when state transitions follow specific rules. Combine with Context for cross-component state sharing.

```typescript
import { createContext, useContext, useReducer, type Dispatch } from 'react';

// State definition
interface MarketState {
  readonly symbols: readonly string[];
  readonly prices: Readonly<Record<string, number>>;
  readonly selectedSymbol: string | null;
  readonly isLoading: boolean;
  readonly error: string | null;
}

const INITIAL_STATE: MarketState = {
  symbols: [],
  prices: {},
  selectedSymbol: null,
  isLoading: false,
  error: null,
};

// Discriminated union for actions
type MarketAction =
  | { readonly type: 'FETCH_START' }
  | { readonly type: 'FETCH_SUCCESS'; readonly payload: { symbols: string[]; prices: Record<string, number> } }
  | { readonly type: 'FETCH_ERROR'; readonly payload: string }
  | { readonly type: 'SELECT_SYMBOL'; readonly payload: string }
  | { readonly type: 'UPDATE_PRICE'; readonly payload: { symbol: string; price: number } };

// Pure reducer — no side effects, returns new state
function marketReducer(state: MarketState, action: MarketAction): MarketState {
  switch (action.type) {
    case 'FETCH_START':
      return { ...state, isLoading: true, error: null };

    case 'FETCH_SUCCESS':
      return {
        ...state,
        isLoading: false,
        symbols: action.payload.symbols,
        prices: action.payload.prices,
      };

    case 'FETCH_ERROR':
      return { ...state, isLoading: false, error: action.payload };

    case 'SELECT_SYMBOL':
      return { ...state, selectedSymbol: action.payload };

    case 'UPDATE_PRICE':
      return {
        ...state,
        prices: {
          ...state.prices,
          [action.payload.symbol]: action.payload.price,
        },
      };
  }
}

// Context setup
interface MarketContextValue {
  readonly state: MarketState;
  readonly dispatch: Dispatch<MarketAction>;
}

const MarketContext = createContext<MarketContextValue | null>(null);

function useMarket(): MarketContextValue {
  const context = useContext(MarketContext);
  if (!context) {
    throw new Error('useMarket must be used within a MarketProvider');
  }
  return context;
}

// Provider component
function MarketProvider({ children }: { readonly children: React.ReactNode }): React.JSX.Element {
  const [state, dispatch] = useReducer(marketReducer, INITIAL_STATE);

  return (
    <MarketContext.Provider value={{ state, dispatch }}>
      {children}
    </MarketContext.Provider>
  );
}

// Consumer component
function SymbolList(): React.JSX.Element {
  const { state, dispatch } = useMarket();

  if (state.isLoading) {
    return <Spinner />;
  }

  if (state.error) {
    return <ErrorMessage message={state.error} />;
  }

  return (
    <ul>
      {state.symbols.map((symbol) => (
        <li
          key={symbol}
          className={symbol === state.selectedSymbol ? 'selected' : ''}
          onClick={() => dispatch({ type: 'SELECT_SYMBOL', payload: symbol })}
        >
          {symbol}: ${state.prices[symbol]?.toFixed(2) ?? 'N/A'}
        </li>
      ))}
    </ul>
  );
}
```

## Async Data Fetching Hook

A reusable hook for fetching data with loading, error, and refetch support.

```typescript
import { useState, useEffect, useCallback, useRef } from 'react';

interface UseQueryOptions {
  readonly enabled?: boolean;
  readonly refetchIntervalMs?: number;
}

interface UseQueryResult<T> {
  readonly data: T | null;
  readonly isLoading: boolean;
  readonly error: string | null;
  readonly refetch: () => Promise<void>;
}

function useQuery<T>(
  queryKey: string,
  queryFn: () => Promise<T>,
  options: UseQueryOptions = {},
): UseQueryResult<T> {
  const { enabled = true, refetchIntervalMs } = options;

  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Ref to track if the component is still mounted
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await queryFn();
      if (mountedRef.current) {
        setData(result);
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      }
    } finally {
      if (mountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [queryFn]);

  // Initial fetch and refetch on key change
  useEffect(() => {
    if (enabled) {
      fetchData();
    }
  }, [queryKey, enabled, fetchData]);

  // Optional polling
  useEffect(() => {
    if (!enabled || !refetchIntervalMs) {
      return;
    }

    const interval = setInterval(fetchData, refetchIntervalMs);
    return () => clearInterval(interval);
  }, [enabled, refetchIntervalMs, fetchData]);

  return { data, isLoading, error, refetch: fetchData };
}

// Usage
function UserDashboard({ userId }: { readonly userId: string }): React.JSX.Element {
  const { data: user, isLoading, error, refetch } = useQuery(
    `user-${userId}`,
    () => fetchUser(userId),
    { enabled: Boolean(userId) },
  );

  if (isLoading) return <Spinner />;
  if (error) return <ErrorMessage message={error} onRetry={refetch} />;
  if (!user) return <EmptyState message="User not found" />;

  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.email}</p>
      <button onClick={refetch}>Refresh</button>
    </div>
  );
}
```
