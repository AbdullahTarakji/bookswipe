import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/providers.dart';
import '../widgets/book_list_tile.dart';
import '../widgets/error_view.dart';
import '../widgets/loading_indicator.dart';

/// Displays the user's liked books with pull-to-refresh and swipe-to-unlike.
class LikedBooksScreen extends ConsumerWidget {
  const LikedBooksScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final likedAsync = ref.watch(likedBooksProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Liked Books'),
      ),
      body: likedAsync.when(
        loading: () => const LoadingIndicator(message: 'Loading liked books...'),
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
                    Icons.favorite_border,
                    size: 80,
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'No liked books yet',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Swipe right on books you like!',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () async {
              ref.read(likedBooksProvider.notifier).refresh();
            },
            child: ListView.separated(
              itemCount: books.length,
              separatorBuilder: (_, _) => const Divider(height: 1),
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
