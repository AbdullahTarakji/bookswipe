// Input validation functions for BookSwipe forms.
//
// These validators mirror the backend validation rules to provide
// immediate client-side feedback before requests are sent.

/// Validates that the given [value] is a properly formatted email address.
///
/// Returns an error message string if validation fails, or `null` if valid.
String? validateEmail(String? value) {
  if (value == null || value.trim().isEmpty) {
    return 'Please enter your email';
  }

  // RFC 5322 simplified pattern: local@domain with at least one dot in domain.
  final emailRegex = RegExp(
    r'^[a-zA-Z0-9.!#$%&*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$',
  );

  if (!emailRegex.hasMatch(value.trim())) {
    return 'Please enter a valid email address';
  }

  return null;
}

/// Validates that the given [value] meets password strength requirements.
///
/// Requirements:
/// - At least 8 characters long
/// - Contains at least one uppercase letter
/// - Contains at least one lowercase letter
/// - Contains at least one digit
///
/// Returns an error message string if validation fails, or `null` if valid.
String? validatePassword(String? value) {
  if (value == null || value.isEmpty) {
    return 'Please enter a password';
  }

  if (value.length < 8) {
    return 'Password must be at least 8 characters';
  }

  if (!RegExp(r'[A-Z]').hasMatch(value)) {
    return 'Password must contain at least one uppercase letter';
  }

  if (!RegExp(r'[a-z]').hasMatch(value)) {
    return 'Password must contain at least one lowercase letter';
  }

  if (!RegExp(r'[0-9]').hasMatch(value)) {
    return 'Password must contain at least one number';
  }

  return null;
}

/// Validates that [value] matches the [password].
///
/// Returns an error message if the values do not match, or `null` if they do.
String? validatePasswordMatch(String? value, String password) {
  if (value == null || value.isEmpty) {
    return 'Please confirm your password';
  }

  if (value != password) {
    return 'Passwords do not match';
  }

  return null;
}

/// Returns a strength assessment for the given [password].
///
/// Strength is classified as:
/// - `'weak'`     -- fewer than 8 characters or missing required character types
/// - `'moderate'` -- meets minimum requirements (8+ chars, mixed case, digit)
/// - `'strong'`   -- 12+ characters with mixed case, digit, and special character
String getPasswordStrength(String password) {
  if (password.length < 8) return 'weak';

  final hasUppercase = RegExp(r'[A-Z]').hasMatch(password);
  final hasLowercase = RegExp(r'[a-z]').hasMatch(password);
  final hasDigit = RegExp(r'[0-9]').hasMatch(password);
  final hasSpecial = RegExp(r'[!@#$%^&*(),.?":{}|<>]').hasMatch(password);

  // Missing any of the three core requirements means weak.
  if (!hasUppercase || !hasLowercase || !hasDigit) return 'weak';

  // 12+ characters with all four character types is strong.
  if (password.length >= 12 && hasSpecial) return 'strong';

  return 'moderate';
}
