# React Components

## Component Structure with Typed Props

Every component gets a dedicated props interface. Export the interface for reuse. Use destructuring in the function signature.

```tsx
interface UserProfileProps {
  readonly user: User;
  readonly showAvatar?: boolean;
  readonly onEdit: (userId: string) => void;
}

function UserProfile({ user, showAvatar = true, onEdit }: UserProfileProps): React.JSX.Element {
  return (
    <div className="user-profile">
      {showAvatar && <Avatar src={user.avatarUrl} alt={user.name} />}
      <h2>{user.name}</h2>
      <p>{user.email}</p>
      <button onClick={() => onEdit(user.id)}>Edit Profile</button>
    </div>
  );
}
```

## Composition Over Inheritance

Build complex UIs by composing small, focused components. Use `children` and named slots instead of monolithic components with many props.

```tsx
// BAD — monolithic component with prop explosion
<Card
  title="Dashboard"
  subtitle="Overview"
  headerIcon={<Icon name="chart" />}
  bodyContent={<Stats data={stats} />}
  footerLeft={<Button>Cancel</Button>}
  footerRight={<Button>Save</Button>}
  showBorder
  variant="elevated"
/>

// GOOD — composable components
interface CardProps {
  readonly children: React.ReactNode;
  readonly variant?: 'flat' | 'elevated';
}

function Card({ children, variant = 'flat' }: CardProps): React.JSX.Element {
  return <div className={`card card--${variant}`}>{children}</div>;
}

interface CardHeaderProps {
  readonly icon?: React.ReactNode;
  readonly children: React.ReactNode;
}

function CardHeader({ icon, children }: CardHeaderProps): React.JSX.Element {
  return (
    <div className="card-header">
      {icon && <span className="card-header__icon">{icon}</span>}
      {children}
    </div>
  );
}

function CardBody({ children }: { readonly children: React.ReactNode }): React.JSX.Element {
  return <div className="card-body">{children}</div>;
}

function CardFooter({ children }: { readonly children: React.ReactNode }): React.JSX.Element {
  return <div className="card-footer">{children}</div>;
}

// Usage — flexible, readable, composable
<Card variant="elevated">
  <CardHeader icon={<Icon name="chart" />}>
    <h2>Dashboard</h2>
    <p>Overview</p>
  </CardHeader>
  <CardBody>
    <Stats data={stats} />
  </CardBody>
  <CardFooter>
    <Button>Cancel</Button>
    <Button>Save</Button>
  </CardFooter>
</Card>
```

## Compound Components Pattern

Use React Context to share implicit state between related components. The parent manages state; children consume it.

```tsx
import { createContext, useContext, useState, useCallback } from 'react';

// Context for shared state
interface TabsContextValue {
  readonly activeTab: string;
  readonly setActiveTab: (id: string) => void;
}

const TabsContext = createContext<TabsContextValue | null>(null);

function useTabsContext(): TabsContextValue {
  const context = useContext(TabsContext);
  if (!context) {
    throw new Error('Tab components must be used within a <Tabs> provider');
  }
  return context;
}

// Parent — owns the state
interface TabsProps {
  readonly defaultTab: string;
  readonly children: React.ReactNode;
  readonly onChange?: (tabId: string) => void;
}

function Tabs({ defaultTab, children, onChange }: TabsProps): React.JSX.Element {
  const [activeTab, setActiveTabState] = useState(defaultTab);

  const setActiveTab = useCallback(
    (id: string) => {
      setActiveTabState(id);
      onChange?.(id);
    },
    [onChange],
  );

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className="tabs">{children}</div>
    </TabsContext.Provider>
  );
}

// Tab list — renders tab buttons
function TabList({ children }: { readonly children: React.ReactNode }): React.JSX.Element {
  return <div className="tab-list" role="tablist">{children}</div>;
}

// Individual tab button
interface TabProps {
  readonly id: string;
  readonly children: React.ReactNode;
}

function Tab({ id, children }: TabProps): React.JSX.Element {
  const { activeTab, setActiveTab } = useTabsContext();
  return (
    <button
      role="tab"
      aria-selected={activeTab === id}
      className={`tab ${activeTab === id ? 'tab--active' : ''}`}
      onClick={() => setActiveTab(id)}
    >
      {children}
    </button>
  );
}

// Tab panel — renders content for active tab
interface TabPanelProps {
  readonly id: string;
  readonly children: React.ReactNode;
}

function TabPanel({ id, children }: TabPanelProps): React.JSX.Element | null {
  const { activeTab } = useTabsContext();
  if (activeTab !== id) {
    return null;
  }
  return (
    <div role="tabpanel" className="tab-panel">
      {children}
    </div>
  );
}

// Usage
<Tabs defaultTab="overview" onChange={(tab) => console.log(`Switched to ${tab}`)}>
  <TabList>
    <Tab id="overview">Overview</Tab>
    <Tab id="analytics">Analytics</Tab>
    <Tab id="settings">Settings</Tab>
  </TabList>
  <TabPanel id="overview"><OverviewContent /></TabPanel>
  <TabPanel id="analytics"><AnalyticsContent /></TabPanel>
  <TabPanel id="settings"><SettingsContent /></TabPanel>
</Tabs>
```

## Render Props Pattern

Pass a function as a prop to delegate rendering decisions to the consumer. Useful for data-fetching components that separate data logic from presentation.

```tsx
interface DataLoaderProps<T> {
  readonly url: string;
  readonly children: (state: DataLoaderState<T>) => React.ReactNode;
}

interface DataLoaderState<T> {
  readonly data: T | null;
  readonly isLoading: boolean;
  readonly error: string | null;
  readonly refetch: () => void;
}

function DataLoader<T>({ url, children }: DataLoaderProps<T>): React.JSX.Element {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, [url]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return <>{children({ data, isLoading, error, refetch: fetchData })}</>;
}

// Usage — consumer controls rendering
<DataLoader<User[]> url="/api/users">
  {({ data, isLoading, error, refetch }) => {
    if (isLoading) return <Spinner />;
    if (error) return <ErrorMessage message={error} onRetry={refetch} />;
    if (!data) return null;
    return <UserList users={data} />;
  }}
</DataLoader>
```

## Error Boundary Pattern

Class component that catches rendering errors in its subtree. Wrap sections of the UI that can fail independently.

```tsx
import { Component, type ErrorInfo, type ReactNode } from 'react';

interface ErrorBoundaryProps {
  readonly children: ReactNode;
  readonly fallback?: ReactNode;
  readonly onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  readonly hasError: boolean;
  readonly error: Error | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('ErrorBoundary caught:', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  private handleReset = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div role="alert" className="error-boundary">
          <h2>Something went wrong</h2>
          <pre>{this.state.error?.message}</pre>
          <button onClick={this.handleReset}>Try again</button>
        </div>
      );
    }
    return this.props.children;
  }
}

// Usage — isolate failures
<ErrorBoundary
  fallback={<p>Chart failed to load.</p>}
  onError={(error) => reportToSentry(error)}
>
  <ComplexChart data={chartData} />
</ErrorBoundary>
```

## Conditional Rendering

Use early returns and extracted components instead of deeply nested ternaries.

```tsx
// BAD — ternary hell
function Dashboard({ user, data, isLoading, error }: DashboardProps): React.JSX.Element {
  return (
    <div>
      {isLoading ? (
        <Spinner />
      ) : error ? (
        <ErrorMessage message={error} />
      ) : !user ? (
        <LoginPrompt />
      ) : !data ? (
        <EmptyState />
      ) : (
        <DashboardContent user={user} data={data} />
      )}
    </div>
  );
}

// GOOD — early returns with guard clauses
function Dashboard({ user, data, isLoading, error }: DashboardProps): React.JSX.Element {
  if (isLoading) {
    return <Spinner />;
  }

  if (error) {
    return <ErrorMessage message={error} />;
  }

  if (!user) {
    return <LoginPrompt />;
  }

  if (!data || data.length === 0) {
    return <EmptyState />;
  }

  return <DashboardContent user={user} data={data} />;
}
```

## Animation Patterns with Framer Motion

Use `AnimatePresence` for enter/exit animations. Use `layout` prop for smooth layout transitions.

```tsx
import { motion, AnimatePresence } from 'framer-motion';

// Animated list items
interface AnimatedListProps {
  readonly items: readonly ListItem[];
  readonly onRemove: (id: string) => void;
}

function AnimatedList({ items, onRemove }: AnimatedListProps): React.JSX.Element {
  return (
    <ul className="animated-list">
      <AnimatePresence initial={false}>
        {items.map((item) => (
          <motion.li
            key={item.id}
            layout
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
          >
            <span>{item.label}</span>
            <button onClick={() => onRemove(item.id)}>Remove</button>
          </motion.li>
        ))}
      </AnimatePresence>
    </ul>
  );
}

// Animated modal
interface ModalProps {
  readonly isOpen: boolean;
  readonly onClose: () => void;
  readonly children: React.ReactNode;
}

function Modal({ isOpen, onClose, children }: ModalProps): React.JSX.Element {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            className="modal-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.5 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.div
            className="modal-content"
            role="dialog"
            aria-modal="true"
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          >
            {children}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
```
