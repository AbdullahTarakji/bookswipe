import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// A beautiful empty state illustration with a message and optional action.
///
/// Used across the app to communicate that there is no content to display,
/// such as no books found, no favorites yet, or no search results.
class EmptyState extends StatelessWidget {
  /// The icon displayed in the illustration circle.
  final IconData icon;

  /// The primary title text.
  final String title;

  /// The secondary subtitle/description text.
  final String subtitle;

  /// Optional action button label. If provided with [onAction], a button is shown.
  final String? actionLabel;

  /// Optional callback invoked when the action button is tapped.
  final VoidCallback? onAction;

  /// Optional action button icon.
  final IconData? actionIcon;

  /// Creates an empty state widget.
  const EmptyState({
    super.key,
    required this.icon,
    required this.title,
    required this.subtitle,
    this.actionLabel,
    this.onAction,
    this.actionIcon,
  });

  /// Empty state for when no books are found in discovery.
  const EmptyState.noBooks({
    super.key,
    this.onAction,
  })  : icon = Icons.auto_stories_rounded,
        title = 'No more books!',
        subtitle = 'Try a different category or check back later.',
        actionLabel = 'Refresh',
        actionIcon = Icons.refresh_rounded;

  /// Empty state for when the user has no favorites yet.
  const EmptyState.noFavorites({
    super.key,
    this.onAction,
  })  : icon = Icons.favorite_border_rounded,
        title = 'No matches yet',
        subtitle = 'Swipe right on books you love\nand they\'ll appear here!',
        actionLabel = 'Discover Books',
        actionIcon = Icons.local_fire_department_rounded;

  /// Empty state for when a search returns no results.
  const EmptyState.noSearchResults({
    super.key,
    this.onAction,
  })  : icon = Icons.search_off_rounded,
        title = 'No results found',
        subtitle = 'Try different keywords or browse categories.',
        actionLabel = 'Clear Search',
        actionIcon = Icons.clear_rounded;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Decorative icon with gradient background circle
            Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  colors: [
                    AppTheme.brandPink.withValues(alpha: 0.12),
                    AppTheme.brandOrange.withValues(alpha: 0.12),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
              ),
              child: ShaderMask(
                shaderCallback: (bounds) =>
                    AppTheme.brandGradient.createShader(bounds),
                child: Icon(
                  icon,
                  size: 56,
                  color: Colors.white,
                ),
              ),
            ),
            const SizedBox(height: 28),
            Text(
              title,
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 10),
            Text(
              subtitle,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: AppTheme.textSecondary,
                height: 1.5,
              ),
              textAlign: TextAlign.center,
            ),
            if (actionLabel != null && onAction != null) ...[
              const SizedBox(height: 28),
              FilledButton.icon(
                onPressed: onAction,
                icon: Icon(actionIcon ?? Icons.arrow_forward_rounded),
                label: Text(actionLabel!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
