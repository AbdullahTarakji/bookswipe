import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Displays a beautiful error state with an icon, title, message,
/// and an optional retry button.
///
/// Used throughout the app to present network errors, load failures,
/// and other error conditions in a user-friendly way.
class ErrorView extends StatelessWidget {
  /// The error message displayed to the user.
  final String message;

  /// Optional callback invoked when the retry button is tapped.
  final VoidCallback? onRetry;

  /// Optional title displayed above the message. Defaults to 'Oops!'.
  final String title;

  /// Optional icon override. Defaults to a cloud-off icon for network errors.
  final IconData icon;

  /// Creates an error view.
  const ErrorView({
    super.key,
    required this.message,
    this.onRetry,
    this.title = 'Oops!',
    this.icon = Icons.cloud_off_rounded,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Decorative error icon with background circle
            Container(
              width: 96,
              height: 96,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: theme.colorScheme.error.withValues(alpha: 0.1),
              ),
              child: Icon(
                icon,
                size: 48,
                color: theme.colorScheme.error,
              ),
            ),
            const SizedBox(height: 24),
            Text(
              title,
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              message,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: AppTheme.textSecondary,
                height: 1.4,
              ),
              textAlign: TextAlign.center,
            ),
            if (onRetry != null) ...[
              const SizedBox(height: 28),
              FilledButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh_rounded),
                label: const Text('Try Again'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
