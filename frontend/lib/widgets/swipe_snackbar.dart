import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Shows a themed floating snackbar notification for swipe actions.
///
/// Provides visual feedback when the user likes, skips, or super-likes
/// a book during discovery swiping.
void showSwipeSnackBar(
  BuildContext context, {
  required String message,
  required IconData icon,
  required Color color,
}) {
  ScaffoldMessenger.of(context).clearSnackBars();
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Row(
        children: [
          Icon(icon, color: Colors.white, size: 20),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
      backgroundColor: color,
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      margin: const EdgeInsets.fromLTRB(16, 0, 16, 16),
      duration: const Duration(milliseconds: 1500),
      dismissDirection: DismissDirection.horizontal,
    ),
  );
}

/// Shows a snackbar for a "liked" swipe action.
void showLikedSnackBar(BuildContext context, String bookTitle) {
  showSwipeSnackBar(
    context,
    message: 'Liked "$bookTitle"',
    icon: Icons.favorite_rounded,
    color: AppTheme.likeGreen,
  );
}

/// Shows a snackbar for a "skipped" swipe action.
void showSkippedSnackBar(BuildContext context, String bookTitle) {
  showSwipeSnackBar(
    context,
    message: 'Skipped "$bookTitle"',
    icon: Icons.close_rounded,
    color: AppTheme.nopeRed.withValues(alpha: 0.85),
  );
}

/// Shows a snackbar for a "super liked" swipe action.
void showSuperLikedSnackBar(BuildContext context, String bookTitle) {
  showSwipeSnackBar(
    context,
    message: 'Super Liked "$bookTitle"',
    icon: Icons.star_rounded,
    color: AppTheme.superLikeBlue,
  );
}

/// Shows a snackbar when a book is added to favorites.
void showAddedToFavoritesSnackBar(BuildContext context, String bookTitle) {
  showSwipeSnackBar(
    context,
    message: '"$bookTitle" added to favorites',
    icon: Icons.bookmark_added_rounded,
    color: AppTheme.likeGreen,
  );
}

/// Shows a snackbar when a book is removed from favorites.
void showRemovedFromFavoritesSnackBar(
  BuildContext context,
  String bookTitle,
) {
  showSwipeSnackBar(
    context,
    message: '"$bookTitle" removed from favorites',
    icon: Icons.bookmark_remove_rounded,
    color: AppTheme.textSecondary,
  );
}
