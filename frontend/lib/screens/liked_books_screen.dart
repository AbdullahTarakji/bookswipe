import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/providers.dart';
import '../theme/app_theme.dart';
import '../widgets/book_list_tile.dart';
import '../widgets/empty_state.dart';
import '../widgets/error_view.dart';
import '../widgets/shimmer_loading.dart';
import '../widgets/swipe_snackbar.dart';

/// Screen displaying the user's liked/favorited books.
///
/// Supports pull-to-refresh, swipe-to-dismiss, shimmer loading skeletons,
/// and snackbar feedback when books are removed.
class LikedBooksScreen extends ConsumerWidget {
  /// Creates the liked books screen.
  const LikedBooksScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final likedAsync = ref.watch(likedBooksProvider);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            ShaderMask(
              shaderCallback: (bounds) =>
                  AppTheme.tinderGradient.createShader(bounds),
              child: const Icon(Icons.favorite, size: 22, color: Colors.white),
            ),
            const SizedBox(width: 8),
            const Text('My Matches'),
          ],
        ),
      ),
      body: likedAsync.when(
        loading: () => const FavoritesShimmer(),
        error: (error, _) => ErrorView(
          message: error.toString(),
          onRetry: () => ref.read(likedBooksProvider.notifier).refresh(),
        ),
        data: (books) {
          if (books.isEmpty) {
            return EmptyState.noFavorites(
              onAction: () => context.go('/'),
            );
          }

          return RefreshIndicator(
            color: AppTheme.tinderRed,
            onRefresh: () async {
              ref.read(likedBooksProvider.notifier).refresh();
            },
            child: ListView.separated(
              padding: const EdgeInsets.symmetric(vertical: 8),
              itemCount: books.length,
              separatorBuilder: (_, _) => const SizedBox(height: 2),
              itemBuilder: (context, index) {
                final book = books[index];
                return BookListTile(
                  book: book,
                  onTap: () => context.push('/book/${book.id}'),
                  onDismiss: () {
                    ref
                        .read(likedBooksProvider.notifier)
                        .unlikeBook(book.id);
                    showRemovedFromFavoritesSnackBar(context, book.title);
                  },
                );
              },
            ),
          );
        },
      ),
    );
  }
}
