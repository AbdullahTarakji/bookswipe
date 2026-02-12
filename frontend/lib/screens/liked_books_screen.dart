import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/providers.dart';
import '../theme/app_theme.dart';
import '../widgets/book_list_tile.dart';
import '../widgets/error_view.dart';
import '../widgets/loading_indicator.dart';

class LikedBooksScreen extends ConsumerWidget {
  const LikedBooksScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final likedAsync = ref.watch(likedBooksProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            ShaderMask(
              shaderCallback: (bounds) => AppTheme.tinderGradient.createShader(bounds),
              child: const Icon(Icons.favorite, size: 22, color: Colors.white),
            ),
            const SizedBox(width: 8),
            const Text('My Matches'),
          ],
        ),
      ),
      body: likedAsync.when(
        loading: () => const LoadingIndicator(message: 'Loading your books...'),
        error: (error, _) => ErrorView(
          message: error.toString(),
          onRetry: () => ref.read(likedBooksProvider.notifier).refresh(),
        ),
        data: (books) {
          if (books.isEmpty) {
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.favorite_border_rounded,
                    size: 80,
                    color: theme.colorScheme.onSurfaceVariant.withValues(alpha: 0.3),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'No matches yet',
                    style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Swipe right on books you love!',
                    style: theme.textTheme.bodyMedium?.copyWith(color: AppTheme.textSecondary),
                  ),
                ],
              ),
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
                    ref.read(likedBooksProvider.notifier).unlikeBook(book.id);
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
