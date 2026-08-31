/**
 * Client-side form validation utilities.
 */

export const validateEmail = (email) => {
  const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  if (!email) return 'Email is required';
  if (!pattern.test(email)) return 'Please enter a valid email address';
  return null;
};

export const validatePassword = (password) => {
  if (!password) return 'Password is required';
  if (password.length < 8) return 'Password must be at least 8 characters';
  if (!/[A-Z]/.test(password)) return 'Password must contain an uppercase letter';
  if (!/[a-z]/.test(password)) return 'Password must contain a lowercase letter';
  if (!/\d/.test(password)) return 'Password must contain a number';
  return null;
};

export const validateName = (name) => {
  if (name && name.length > 255) return 'Name must be less than 255 characters';
  return null;
};

export const validateRequired = (value, fieldName) => {
  if (!value || !value.trim()) return `${fieldName} is required`;
  return null;
};
