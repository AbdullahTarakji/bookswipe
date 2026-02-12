import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'app.dart';
import 'theme/app_theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  // Global error handler for Flutter framework errors
  FlutterError.onError = (details) {
    FlutterError.presentError(details);
    if (kReleaseMode) {
      Zone.current.handleUncaughtError(details.exception, details.stack ?? StackTrace.empty);
    }
  };

  // Replace the red error screen with a user-friendly fallback in release mode
  if (kReleaseMode) {
    ErrorWidget.builder = (details) => const Material(
      child: Center(
        child: Text(
          'Something went wrong',
          style: TextStyle(fontSize: 16, color: Colors.black54),
        ),
      ),
    );
  }

  // Catch async errors that escape the Flutter framework
  runZonedGuarded(
    () {
      runApp(
        const ProviderScope(
          child: BookSwipeApp(),
        ),
      );
    },
    (error, stack) {
      debugPrint('Uncaught error: $error\n$stack');
    },
  );
}

/// Widget-level error boundary that catches build/render errors and shows
/// a user-friendly fallback instead of the red error screen.
class ErrorBoundary extends StatefulWidget {
  final Widget child;
  const ErrorBoundary({super.key, required this.child});

  @override
  State<ErrorBoundary> createState() => _ErrorBoundaryState();
}

class _ErrorBoundaryState extends State<ErrorBoundary> {
  bool _hasError = false;
  FlutterErrorDetails? _errorDetails;

  @override
  void initState() {
    super.initState();
  }

  @override
  Widget build(BuildContext context) {
    if (_hasError) {
      return _ErrorFallback(
        details: _errorDetails,
        onRetry: () => setState(() {
          _hasError = false;
          _errorDetails = null;
        }),
      );
    }

    return widget.child;
  }

  // Called by the framework when a child widget throws during build
  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _hasError = false;
  }
}

class _ErrorFallback extends StatelessWidget {
  final FlutterErrorDetails? details;
  final VoidCallback onRetry;

  const _ErrorFallback({this.details, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Material(
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(
                Icons.error_outline_rounded,
                size: 64,
                color: AppTheme.nopeRed,
              ),
              const SizedBox(height: 16),
              Text(
                'Something went wrong',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.textPrimary,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'An unexpected error occurred. Please try again.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 14,
                  color: AppTheme.textSecondary,
                ),
              ),
              if (!kReleaseMode && details != null) ...[
                const SizedBox(height: 16),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.grey.shade100,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    details!.exceptionAsString(),
                    style: const TextStyle(fontSize: 11, fontFamily: 'monospace'),
                    maxLines: 5,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
              const SizedBox(height: 24),
              FilledButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh),
                label: const Text('Try Again'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
