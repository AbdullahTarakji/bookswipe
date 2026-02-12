import 'package:flutter/material.dart';

/// Utility for showing consistent snackbar/toast messages across the app.
class SnackbarUtils {
  /// Show an error snackbar with a red background.
  static void showError(BuildContext context, String message) {
    _show(
      context,
      message: message,
      backgroundColor: Theme.of(context).colorScheme.error,
      icon: Icons.error_outline,
    );
  }

  /// Show a success snackbar with a green background.
  static void showSuccess(BuildContext context, String message) {
    _show(
      context,
      message: message,
      backgroundColor: const Color(0xFF4CAF50),
      icon: Icons.check_circle_outline,
    );
  }

  /// Show an informational snackbar.
  static void showInfo(BuildContext context, String message) {
    _show(
      context,
      message: message,
      backgroundColor: Theme.of(context).colorScheme.primary,
      icon: Icons.info_outline,
    );
  }

  static void _show(
    BuildContext context, {
    required String message,
    required Color backgroundColor,
    required IconData icon,
    Duration duration = const Duration(seconds: 3),
  }) {
    ScaffoldMessenger.of(context).clearSnackBars();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(icon, color: Colors.white, size: 20),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                message,
                style: const TextStyle(color: Colors.white),
              ),
            ),
          ],
        ),
        backgroundColor: backgroundColor,
        behavior: SnackBarBehavior.floating,
        duration: duration,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
    );
  }
}
