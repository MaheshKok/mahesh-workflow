# TypeScript Standards

## Variable Naming Conventions

Use descriptive, meaningful names. Boolean variables use `is/has/should` prefixes. Collections use plural nouns.

```typescript
// BAD
const d = new Date();
const flag = true;
const list = ['a', 'b'];
const val = getUserName();

// GOOD
const createdAt = new Date();
const isVisible = true;
const userNames = ['alice', 'bob'];
const userName = getUserName();
```

## Function Naming Conventions

Use verb-noun pattern. Event handlers use `handle` prefix. Async functions indicate the operation.

```typescript
// BAD
function data() { ... }
function click() { ... }
function process() { ... }

// GOOD
function fetchMarketData(): Promise<MarketData> { ... }
function handleButtonClick(event: MouseEvent): void { ... }
function validateUserInput(input: string): ValidationResult { ... }
function calculateTotalPrice(items: CartItem[]): number { ... }
function parseConfigFile(path: string): Config { ... }
```

## Immutability (CRITICAL)

Never mutate objects or arrays. Always create new copies with spread operator.

```typescript
// BAD — mutates the original object
function updateUser(user: User, name: string): User {
  user.name = name; // MUTATION
  return user;
}

// GOOD — returns a new object
function updateUser(user: User, name: string): User {
  return { ...user, name };
}

// BAD — mutates the array
function addItem(items: Item[], newItem: Item): Item[] {
  items.push(newItem); // MUTATION
  return items;
}

// GOOD — returns a new array
function addItem(items: readonly Item[], newItem: Item): Item[] {
  return [...items, newItem];
}

// Removing from array immutably
function removeItem(items: readonly Item[], id: string): Item[] {
  return items.filter((item) => item.id !== id);
}

// Updating nested objects immutably
function updateAddress(user: User, city: string): User {
  return {
    ...user,
    address: { ...user.address, city },
  };
}
```

## Error Handling Patterns

Handle errors at every level. Provide context-rich error messages. Never swallow errors silently.

```typescript
// Custom error class with cause chaining
class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number = 500,
    options?: ErrorOptions,
  ) {
    super(message, options);
    this.name = 'AppError';
  }
}

// Service-layer error handling
async function fetchUser(userId: string): Promise<User> {
  if (!userId.trim()) {
    throw new AppError('User ID is required', 'INVALID_INPUT', 400);
  }

  try {
    const response = await fetch(`/api/users/${userId}`);

    if (!response.ok) {
      throw new AppError(
        `Failed to fetch user: ${response.statusText}`,
        'FETCH_FAILED',
        response.status,
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof AppError) {
      throw error;
    }
    throw new AppError(
      'Unexpected error while fetching user',
      'INTERNAL_ERROR',
      500,
      { cause: error },
    );
  }
}

// Guard clause pattern — early returns reduce nesting
function processOrder(order: Order | null): OrderResult {
  if (!order) {
    return { success: false, error: 'Order is required' };
  }
  if (order.items.length === 0) {
    return { success: false, error: 'Order must have at least one item' };
  }
  if (order.status !== 'pending') {
    return { success: false, error: `Cannot process order in ${order.status} state` };
  }

  const total = calculateTotal(order.items);
  return { success: true, data: { orderId: order.id, total } };
}
```

## Async/Await Best Practices

Use Promise.all for independent operations. Avoid sequential awaits when parallelism is possible.

```typescript
// BAD — sequential when operations are independent
async function loadDashboard(userId: string): Promise<Dashboard> {
  const user = await fetchUser(userId);
  const orders = await fetchOrders(userId);
  const notifications = await fetchNotifications(userId);
  return { user, orders, notifications };
}

// GOOD — parallel execution with Promise.all
async function loadDashboard(userId: string): Promise<Dashboard> {
  const [user, orders, notifications] = await Promise.all([
    fetchUser(userId),
    fetchOrders(userId),
    fetchNotifications(userId),
  ]);
  return { user, orders, notifications };
}

// GOOD — Promise.allSettled when partial failure is acceptable
async function loadWidgets(widgetIds: string[]): Promise<WidgetResult[]> {
  const results = await Promise.allSettled(
    widgetIds.map((id) => fetchWidget(id)),
  );

  return results.map((result, index) => {
    if (result.status === 'fulfilled') {
      return { id: widgetIds[index], data: result.value, error: null };
    }
    return { id: widgetIds[index], data: null, error: result.reason.message };
  });
}
```

## Type Safety

Define interfaces for all data structures. Avoid `any`. Use discriminated unions for variant types.

```typescript
// BAD — using any
function processData(data: any): any {
  return data.items.map((item: any) => item.name);
}

// GOOD — properly typed
interface Product {
  readonly id: string;
  readonly name: string;
  readonly price: number;
  readonly category: ProductCategory;
}

type ProductCategory = 'electronics' | 'clothing' | 'food';

function getProductNames(products: readonly Product[]): string[] {
  return products.map((product) => product.name);
}

// Discriminated unions for variant types
interface SuccessResult {
  readonly status: 'success';
  readonly data: User;
}

interface ErrorResult {
  readonly status: 'error';
  readonly error: string;
  readonly code: number;
}

type Result = SuccessResult | ErrorResult;

function handleResult(result: Result): void {
  switch (result.status) {
    case 'success':
      console.log(result.data.name); // TypeScript knows data exists
      break;
    case 'error':
      console.error(`Error ${result.code}: ${result.error}`);
      break;
  }
}

// Generic utility types
type ReadonlyDeep<T> = {
  readonly [K in keyof T]: T[K] extends object ? ReadonlyDeep<T[K]> : T[K];
};
```

## API Design Standards

Use consistent response envelopes, Zod validation, and RESTful conventions.

```typescript
import { z } from 'zod';

// Zod schema for input validation
const CreateUserSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  role: z.enum(['admin', 'user', 'viewer']),
  age: z.number().int().min(18).max(120).optional(),
});

type CreateUserInput = z.infer<typeof CreateUserSchema>;

// Consistent API response format
interface ApiResponse<T> {
  readonly success: boolean;
  readonly data: T | null;
  readonly error: string | null;
  readonly meta?: {
    readonly total: number;
    readonly page: number;
    readonly limit: number;
  };
}

function createSuccessResponse<T>(data: T, meta?: ApiResponse<T>['meta']): ApiResponse<T> {
  return { success: true, data, error: null, meta };
}

function createErrorResponse(error: string): ApiResponse<never> {
  return { success: false, data: null, error };
}

// Next.js API route with Zod validation
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json();
    const parsed = CreateUserSchema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json(
        createErrorResponse(parsed.error.issues.map((i) => i.message).join(', ')),
        { status: 400 },
      );
    }

    const user = await createUser(parsed.data);
    return NextResponse.json(createSuccessResponse(user), { status: 201 });
  } catch (error) {
    console.error('Failed to create user:', error);
    return NextResponse.json(
      createErrorResponse('Internal server error'),
      { status: 500 },
    );
  }
}
```

## File Organization

```
src/
  components/          # React components by feature
    user/
      UserProfile.tsx
      UserAvatar.tsx
      user-profile.test.tsx
  hooks/               # Custom hooks
    useDebounce.ts
    useQuery.ts
  lib/                 # Utilities, clients, helpers
    api-client.ts
    validators.ts
  types/               # Shared type definitions
    user.ts
    api.ts
  constants/           # Named constants
    config.ts
```

File naming: PascalCase for components (`UserProfile.tsx`), camelCase for utilities (`apiClient.ts`), kebab-case for config files (`next.config.ts`).

## Comments and Documentation

Use JSDoc for public APIs. Explain "why", not "what". Avoid obvious comments.

```typescript
/**
 * Calculates the weighted moving average of a price series.
 *
 * Uses linearly decreasing weights where the most recent value
 * has the highest weight. Returns null if the series is shorter
 * than the specified period.
 *
 * @param prices - Chronologically ordered price values
 * @param period - Number of periods for the moving average
 * @returns The weighted moving average, or null if insufficient data
 */
function calculateWMA(prices: readonly number[], period: number): number | null {
  if (prices.length < period) {
    return null;
  }

  const slice = prices.slice(-period);
  const weightSum = (period * (period + 1)) / 2;

  // Weight decreases linearly: most recent price gets weight=period,
  // oldest gets weight=1
  return slice.reduce((sum, price, i) => sum + price * (i + 1), 0) / weightSum;
}
```

## Code Smell Detection

Watch for these anti-patterns and refactor immediately.

```typescript
// SMELL: Long function (>50 lines) — extract helpers
// SMELL: Deep nesting (>3 levels) — use early returns
// SMELL: Magic numbers — use named constants

// BAD
if (retries < 3) { ... }
setTimeout(callback, 5000);

// GOOD
const MAX_RETRIES = 3;
const RECONNECT_DELAY_MS = 5_000;

if (retries < MAX_RETRIES) { ... }
setTimeout(callback, RECONNECT_DELAY_MS);

// SMELL: Boolean parameters — use options object
// BAD
function createUser(name: string, isAdmin: boolean, sendEmail: boolean) { ... }

// GOOD
interface CreateUserOptions {
  readonly name: string;
  readonly role: 'admin' | 'user';
  readonly notifyByEmail: boolean;
}
function createUser(options: CreateUserOptions) { ... }
```

## Testing Standards

Use the Arrange-Act-Assert pattern. Descriptive test names. Test behavior, not implementation.

```typescript
import { describe, it, expect } from 'vitest';

describe('calculateWMA', () => {
  it('returns null when prices array is shorter than period', () => {
    // Arrange
    const prices = [10, 20];
    const period = 5;

    // Act
    const result = calculateWMA(prices, period);

    // Assert
    expect(result).toBeNull();
  });

  it('calculates weighted average with linear weights for the given period', () => {
    // Arrange — weights: [1, 2, 3], weightSum = 6
    const prices = [10, 20, 30];
    const period = 3;

    // Act
    const result = calculateWMA(prices, period);

    // Assert — (10*1 + 20*2 + 30*3) / 6 = 140/6 ≈ 23.33
    expect(result).toBeCloseTo(23.33, 2);
  });
});
```
