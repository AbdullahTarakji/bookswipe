import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Tutorial overlay shown on first visit to the swipe screen.
/// Explains swipe left/right gestures, then dismisses on tap.
class SwipeTutorialOverlay extends StatelessWidget {
  final VoidCallback onDismiss;

  const SwipeTutorialOverlay({super.key, required this.onDismiss});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return GestureDetector(
      onTap: onDismiss,
      child: Container(
        color: Colors.black.withValues(alpha: 0.75),
        child: SafeArea(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Left swipe
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.arrow_back_rounded,
                      color: AppTheme.nopeRed, size: 40),
                  const SizedBox(width: 12),
                  Text(
                    'Swipe left to skip',
                    style: theme.textTheme.titleLarge?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 48),
              // Right swipe
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    'Swipe right to like',
                    style: theme.textTheme.titleLarge?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(width: 12),
                  const Icon(Icons.arrow_forward_rounded,
                      color: AppTheme.likeGreen, size: 40),
                ],
              ),
              const SizedBox(height: 64),
              Text(
                'Tap anywhere to start swiping',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: Colors.white70,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
