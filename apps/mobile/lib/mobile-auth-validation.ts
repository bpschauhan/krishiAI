const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const phonePattern = /^(?:\+91)?[6-9]\d{9}$/;

export function normalizeOptionalText(value: string): string | null {
  const trimmed = value.trim();
  return trimmed || null;
}

export function validateRequired(value: string, label: string): string | null {
  return value.trim() ? null : `${label} is required.`;
}

export function validateEmail(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) {
    return "Email is required.";
  }
  return emailPattern.test(trimmed) ? null : "Enter a valid email address.";
}

export function validatePassword(value: string): string | null {
  if (!value) {
    return "Password is required.";
  }
  return value.length >= 8 ? null : "Password must be at least 8 characters.";
}

export function validateIndianPhone(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  const normalized = trimmed.replace(/[\s-]/g, "");
  return phonePattern.test(normalized) ? null : "Enter a valid Indian mobile number.";
}
