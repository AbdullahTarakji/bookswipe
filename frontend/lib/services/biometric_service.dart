import 'package:local_auth/local_auth.dart';

/// Biometric authentication infrastructure for BookSwipe.
///
/// This service wraps the `local_auth` package to provide a clean
/// interface for checking biometric availability and authenticating
/// users via fingerprint, face recognition, or device credentials.
///
/// This is scaffolding -- full integration with the auth flow
/// (e.g., gating app access behind biometrics on resume) should be
/// added once the core auth system is complete.
class BiometricService {
  final LocalAuthentication _localAuth = LocalAuthentication();

  /// Checks whether biometric authentication is available on the device.
  ///
  /// Returns `true` if:
  /// - The device hardware supports biometrics, AND
  /// - At least one biometric credential is enrolled.
  ///
  /// Returns `false` otherwise, or if an error occurs during the check.
  Future<bool> isBiometricAvailable() async {
    try {
      final isDeviceSupported = await _localAuth.isDeviceSupported();
      if (!isDeviceSupported) return false;

      final canCheckBiometrics = await _localAuth.canCheckBiometrics;
      if (!canCheckBiometrics) return false;

      final availableBiometrics = await _localAuth.getAvailableBiometrics();
      return availableBiometrics.isNotEmpty;
    } catch (e) {
      return false;
    }
  }

  /// Prompts the user to authenticate using biometrics or device credentials.
  ///
  /// Returns a [BiometricResult] indicating success or the reason for failure.
  ///
  /// The [reason] parameter is displayed to the user in the system biometric
  /// dialog to explain why authentication is required.
  Future<BiometricResult> authenticate({
    String reason = 'Please authenticate to access BookSwipe',
  }) async {
    try {
      final isAvailable = await isBiometricAvailable();
      if (!isAvailable) {
        return BiometricResult(
          success: false,
          errorMessage: 'Biometric authentication is not available on this device',
        );
      }

      final didAuthenticate = await _localAuth.authenticate(
        localizedReason: reason,
        options: const AuthenticationOptions(
          stickyAuth: true,
          biometricOnly: false, // Allow PIN/pattern as fallback
        ),
      );

      if (didAuthenticate) {
        return BiometricResult(success: true);
      } else {
        return BiometricResult(
          success: false,
          errorMessage: 'Authentication failed or was cancelled',
        );
      }
    } catch (e) {
      return BiometricResult(
        success: false,
        errorMessage: 'Biometric authentication error: ${e.toString()}',
      );
    }
  }

  /// Returns the type of biometric authentication available on the device.
  ///
  /// Possible return values:
  /// - [BiometricType.face]        -- Face recognition (Face ID on iOS)
  /// - [BiometricType.fingerprint] -- Fingerprint sensor (Touch ID on iOS)
  /// - [BiometricType.iris]        -- Iris scanner
  /// - [BiometricType.strong]      -- Strong biometric (Android)
  /// - [BiometricType.weak]        -- Weak biometric (Android)
  /// - `null`                      -- No biometrics available
  Future<BiometricType?> getBiometricType() async {
    try {
      final availableBiometrics = await _localAuth.getAvailableBiometrics();

      if (availableBiometrics.isEmpty) return null;

      // Prefer face recognition, then fingerprint, then whatever is first.
      if (availableBiometrics.contains(BiometricType.face)) {
        return BiometricType.face;
      }
      if (availableBiometrics.contains(BiometricType.fingerprint)) {
        return BiometricType.fingerprint;
      }
      return availableBiometrics.first;
    } catch (e) {
      return null;
    }
  }
}

/// Result of a biometric authentication attempt.
class BiometricResult {
  /// Whether authentication succeeded.
  final bool success;

  /// A human-readable error message when [success] is `false`.
  /// Will be `null` when [success] is `true`.
  final String? errorMessage;

  const BiometricResult({
    required this.success,
    this.errorMessage,
  });

  @override
  String toString() =>
      'BiometricResult(success: $success, errorMessage: $errorMessage)';
}
