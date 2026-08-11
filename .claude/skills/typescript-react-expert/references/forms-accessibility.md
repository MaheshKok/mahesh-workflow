# Forms & Accessibility

## Controlled Form with Validation

Use typed state for form data and errors. Validate on submit and optionally on blur. Show inline error messages tied to their fields with `aria-describedby`.

```tsx
import { useState, useCallback, type FormEvent } from 'react';

interface FormData {
  readonly name: string;
  readonly email: string;
  readonly password: string;
  readonly confirmPassword: string;
}

interface FormErrors {
  readonly name?: string;
  readonly email?: string;
  readonly password?: string;
  readonly confirmPassword?: string;
}

const INITIAL_FORM_DATA: FormData = {
  name: '',
  email: '',
  password: '',
  confirmPassword: '',
};

const MIN_PASSWORD_LENGTH = 8;

// Email validation regex: standard RFC 5322 simplified pattern
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validate(data: FormData): FormErrors {
  const errors: Partial<Record<keyof FormData, string>> = {};

  if (!data.name.trim()) {
    errors.name = 'Name is required';
  }

  if (!data.email.trim()) {
    errors.email = 'Email is required';
  } else if (!EMAIL_REGEX.test(data.email)) {
    errors.email = 'Please enter a valid email address';
  }

  if (!data.password) {
    errors.password = 'Password is required';
  } else if (data.password.length < MIN_PASSWORD_LENGTH) {
    errors.password = `Password must be at least ${MIN_PASSWORD_LENGTH} characters`;
  }

  if (data.confirmPassword !== data.password) {
    errors.confirmPassword = 'Passwords do not match';
  }

  return errors;
}

function hasErrors(errors: FormErrors): boolean {
  return Object.values(errors).some(Boolean);
}

interface SignUpFormProps {
  readonly onSubmit: (data: FormData) => Promise<void>;
}

function SignUpForm({ onSubmit }: SignUpFormProps): React.JSX.Element {
  const [formData, setFormData] = useState<FormData>(INITIAL_FORM_DATA);
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const updateField = useCallback(
    (field: keyof FormData, value: string) => {
      setFormData((prev) => ({ ...prev, [field]: value }));
      // Clear field error on change
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    },
    [],
  );

  const handleBlur = useCallback(
    (field: keyof FormData) => {
      const fieldErrors = validate(formData);
      if (fieldErrors[field]) {
        setErrors((prev) => ({ ...prev, [field]: fieldErrors[field] }));
      }
    },
    [formData],
  );

  const handleSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      setSubmitError(null);

      const validationErrors = validate(formData);
      setErrors(validationErrors);

      if (hasErrors(validationErrors)) {
        return;
      }

      setIsSubmitting(true);
      try {
        await onSubmit(formData);
      } catch (error) {
        setSubmitError(
          error instanceof Error ? error.message : 'An unexpected error occurred',
        );
      } finally {
        setIsSubmitting(false);
      }
    },
    [formData, onSubmit],
  );

  return (
    <form onSubmit={handleSubmit} noValidate aria-label="Sign up form">
      {submitError && (
        <div role="alert" className="form-error-banner">
          {submitError}
        </div>
      )}

      <FormField
        label="Name"
        name="name"
        value={formData.name}
        error={errors.name}
        onChange={(value) => updateField('name', value)}
        onBlur={() => handleBlur('name')}
        required
      />

      <FormField
        label="Email"
        name="email"
        type="email"
        value={formData.email}
        error={errors.email}
        onChange={(value) => updateField('email', value)}
        onBlur={() => handleBlur('email')}
        required
      />

      <FormField
        label="Password"
        name="password"
        type="password"
        value={formData.password}
        error={errors.password}
        onChange={(value) => updateField('password', value)}
        onBlur={() => handleBlur('password')}
        required
      />

      <FormField
        label="Confirm Password"
        name="confirmPassword"
        type="password"
        value={formData.confirmPassword}
        error={errors.confirmPassword}
        onChange={(value) => updateField('confirmPassword', value)}
        onBlur={() => handleBlur('confirmPassword')}
        required
      />

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Creating account...' : 'Sign Up'}
      </button>
    </form>
  );
}

// Reusable form field with accessible error binding
interface FormFieldProps {
  readonly label: string;
  readonly name: string;
  readonly type?: string;
  readonly value: string;
  readonly error?: string;
  readonly required?: boolean;
  readonly onChange: (value: string) => void;
  readonly onBlur: () => void;
}

function FormField({
  label,
  name,
  type = 'text',
  value,
  error,
  required = false,
  onChange,
  onBlur,
}: FormFieldProps): React.JSX.Element {
  const errorId = `${name}-error`;

  return (
    <div className="form-field">
      <label htmlFor={name}>
        {label}
        {required && <span aria-hidden="true"> *</span>}
      </label>
      <input
        id={name}
        name={name}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onBlur={onBlur}
        aria-required={required}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : undefined}
        className={error ? 'input--error' : ''}
      />
      {error && (
        <p id={errorId} className="field-error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
```

## Keyboard Navigation

Implement full keyboard support for custom interactive components. Support standard patterns: ArrowDown/Up for lists, Enter to select, Escape to close.

```tsx
import { useState, useRef, useCallback, useEffect, type KeyboardEvent } from 'react';

interface DropdownOption {
  readonly id: string;
  readonly label: string;
}

interface DropdownProps {
  readonly label: string;
  readonly options: readonly DropdownOption[];
  readonly value: string | null;
  readonly onChange: (optionId: string) => void;
}

function Dropdown({ label, options, value, onChange }: DropdownProps): React.JSX.Element {
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  const selectedOption = options.find((opt) => opt.id === value);

  const openDropdown = useCallback(() => {
    setIsOpen(true);
    setHighlightedIndex(value ? options.findIndex((opt) => opt.id === value) : 0);
  }, [options, value]);

  const closeDropdown = useCallback(() => {
    setIsOpen(false);
    setHighlightedIndex(-1);
    buttonRef.current?.focus();
  }, []);

  const selectOption = useCallback(
    (optionId: string) => {
      onChange(optionId);
      closeDropdown();
    },
    [onChange, closeDropdown],
  );

  const handleButtonKeyDown = useCallback(
    (event: KeyboardEvent<HTMLButtonElement>) => {
      switch (event.key) {
        case 'ArrowDown':
        case 'ArrowUp':
        case 'Enter':
        case ' ':
          event.preventDefault();
          openDropdown();
          break;
      }
    },
    [openDropdown],
  );

  const handleListKeyDown = useCallback(
    (event: KeyboardEvent<HTMLUListElement>) => {
      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          setHighlightedIndex((prev) =>
            prev < options.length - 1 ? prev + 1 : 0,
          );
          break;

        case 'ArrowUp':
          event.preventDefault();
          setHighlightedIndex((prev) =>
            prev > 0 ? prev - 1 : options.length - 1,
          );
          break;

        case 'Enter':
        case ' ':
          event.preventDefault();
          if (highlightedIndex >= 0) {
            selectOption(options[highlightedIndex].id);
          }
          break;

        case 'Escape':
          event.preventDefault();
          closeDropdown();
          break;

        case 'Home':
          event.preventDefault();
          setHighlightedIndex(0);
          break;

        case 'End':
          event.preventDefault();
          setHighlightedIndex(options.length - 1);
          break;
      }
    },
    [options, highlightedIndex, selectOption, closeDropdown],
  );

  // Scroll highlighted option into view
  useEffect(() => {
    if (isOpen && highlightedIndex >= 0 && listRef.current) {
      const highlightedEl = listRef.current.children[highlightedIndex] as HTMLElement;
      highlightedEl?.scrollIntoView({ block: 'nearest' });
    }
  }, [isOpen, highlightedIndex]);

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return;

    function handleClickOutside(event: MouseEvent): void {
      const target = event.target as Node;
      if (!buttonRef.current?.contains(target) && !listRef.current?.contains(target)) {
        closeDropdown();
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen, closeDropdown]);

  const listboxId = `${label.toLowerCase().replace(/\s+/g, '-')}-listbox`;

  return (
    <div className="dropdown">
      <label id={`${listboxId}-label`}>{label}</label>
      <button
        ref={buttonRef}
        type="button"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-labelledby={`${listboxId}-label`}
        onClick={() => (isOpen ? closeDropdown() : openDropdown())}
        onKeyDown={handleButtonKeyDown}
      >
        {selectedOption?.label ?? 'Select an option'}
      </button>

      {isOpen && (
        <ul
          ref={listRef}
          id={listboxId}
          role="listbox"
          aria-labelledby={`${listboxId}-label`}
          aria-activedescendant={
            highlightedIndex >= 0 ? `${listboxId}-option-${highlightedIndex}` : undefined
          }
          tabIndex={0}
          onKeyDown={handleListKeyDown}
        >
          {options.map((option, index) => (
            <li
              key={option.id}
              id={`${listboxId}-option-${index}`}
              role="option"
              aria-selected={option.id === value}
              className={index === highlightedIndex ? 'highlighted' : ''}
              onClick={() => selectOption(option.id)}
              onMouseEnter={() => setHighlightedIndex(index)}
            >
              {option.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

## Focus Management

Trap focus within modals. Restore focus to the trigger element when closing. Use `useRef` to track the previously focused element.

```tsx
import { useEffect, useRef, useCallback, type KeyboardEvent } from 'react';

interface ModalProps {
  readonly isOpen: boolean;
  readonly onClose: () => void;
  readonly title: string;
  readonly children: React.ReactNode;
}

const FOCUSABLE_SELECTOR = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(', ');

function Modal({ isOpen, onClose, title, children }: ModalProps): React.JSX.Element | null {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // Save the element that had focus before the modal opened
  useEffect(() => {
    if (isOpen) {
      previousFocusRef.current = document.activeElement as HTMLElement;
    }
  }, [isOpen]);

  // Focus the first focusable element inside the modal on open
  useEffect(() => {
    if (!isOpen || !modalRef.current) return;

    const focusableElements = modalRef.current.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
    if (focusableElements.length > 0) {
      focusableElements[0].focus();
    } else {
      // If no focusable elements, focus the modal itself
      modalRef.current.focus();
    }
  }, [isOpen]);

  // Restore focus when modal closes
  useEffect(() => {
    if (!isOpen && previousFocusRef.current) {
      previousFocusRef.current.focus();
      previousFocusRef.current = null;
    }
  }, [isOpen]);

  // Trap focus within the modal
  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLDivElement>) => {
      if (event.key === 'Escape') {
        onClose();
        return;
      }

      if (event.key !== 'Tab' || !modalRef.current) return;

      const focusableElements = modalRef.current.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
      if (focusableElements.length === 0) return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (event.shiftKey) {
        // Shift+Tab: if on first element, wrap to last
        if (document.activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        }
      } else {
        // Tab: if on last element, wrap to first
        if (document.activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    },
    [onClose],
  );

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (!isOpen) return;

    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    return () => {
      document.body.style.overflow = originalOverflow;
    };
  }, [isOpen]);

  if (!isOpen) {
    return null;
  }

  const titleId = 'modal-title';

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        ref={modalRef}
        className="modal-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        <header className="modal-header">
          <h2 id={titleId}>{title}</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="modal-close"
          >
            X
          </button>
        </header>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}
```

## ARIA Attributes Quick Reference

Use semantic HTML first. Add ARIA only when native semantics are insufficient.

| Attribute | When to use | Example |
|-----------|-------------|---------|
| `role="alert"` | Dynamic error messages, status changes | `<div role="alert">{error}</div>` |
| `aria-label` | Interactive element with no visible text | `<button aria-label="Close">X</button>` |
| `aria-labelledby` | Label is in a separate element | `<div aria-labelledby="heading-id">` |
| `aria-describedby` | Additional help text or error for an input | `<input aria-describedby="email-error" />` |
| `aria-invalid` | Form field with validation error | `<input aria-invalid={!!error} />` |
| `aria-required` | Required form field | `<input aria-required="true" />` |
| `aria-expanded` | Collapsible content (dropdown, accordion) | `<button aria-expanded={isOpen}>` |
| `aria-haspopup` | Button that opens a menu or listbox | `<button aria-haspopup="listbox">` |
| `aria-selected` | Selected option in a listbox | `<li aria-selected={isSelected}>` |
| `aria-activedescendant` | Currently highlighted option in a composite | `<ul aria-activedescendant={activeId}>` |
| `aria-hidden` | Decorative content to hide from screen readers | `<span aria-hidden="true">*</span>` |
| `aria-live` | Region that updates dynamically | `<div aria-live="polite">Updated</div>` |
| `aria-modal` | Modal dialog that traps focus | `<div role="dialog" aria-modal="true">` |

### Common Patterns

```tsx
// Skip navigation link
<a href="#main-content" className="skip-link">
  Skip to main content
</a>

// Live region for async status updates
<div aria-live="polite" aria-atomic="true" className="sr-only">
  {statusMessage}
</div>

// Visually hidden but screen-reader accessible
<span className="sr-only">
  {accessibleLabel}
</span>

// CSS for sr-only
// .sr-only {
//   position: absolute;
//   width: 1px;
//   height: 1px;
//   padding: 0;
//   margin: -1px;
//   overflow: hidden;
//   clip: rect(0, 0, 0, 0);
//   white-space: nowrap;
//   border-width: 0;
// }
```
