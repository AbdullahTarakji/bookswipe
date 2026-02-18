// cached_network_image removed — using Image.network for web compatibility
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/book.dart';
import '../providers/providers.dart';
import '../providers/social_providers.dart';
import '../widgets/error_view.dart';
import '../widgets/shimmer_loading.dart';
import '../widgets/review_section.dart';
import '../widgets/swipe_snackbar.dart';

/// Full-page book detail screen with Hero cover animation and shimmer loading.
///
/// Navigated to from the liked books list or any book link via `/book/:id`.
/// Uses a [SliverAppBar] with an expanding cover image and displays
/// metadata, categories, description, and a like/unlike button.
class BookDetailScreen extends ConsumerWidget {
  /// The unique identifier of the book to display.
  final String bookId;

  /// Creates a book detail screen for the given [bookId].
  const BookDetailScreen({super.key, required this.bookId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bookAsync = ref.watch(bookDetailProvider(bookId));
    final likedBooks = ref.watch(likedBooksProvider).valueOrNull ?? [];
    final isLiked = likedBooks.any((b) => b.id == bookId);

    return Scaffold(
      body: bookAsync.when(
        loading: () => const BookDetailShimmer(),
        error: (error, _) => ErrorView(
          message: error.toString(),
          onRetry: () => ref.invalidate(bookDetailProvider(bookId)),
        ),
        data: (book) => _buildContent(context, ref, book, isLiked),
      ),
    );
  }

  Widget _buildContent(
    BuildContext context,
    WidgetRef ref,
    Book book,
    bool isLiked,
  ) {
    final theme = Theme.of(context);

    return CustomScrollView(
      slivers: [
        SliverAppBar(
          expandedHeight: 350,
          pinned: true,
          flexibleSpace: FlexibleSpaceBar(
            background: Hero(
              tag: 'book-cover-${book.id}',
              child: book.thumbnailUrl != null
                  ? Image.network(
                      book.highResThumbnail,
                      fit: BoxFit.cover,
                      errorBuilder: (_, _, _) => Container(
                        color: theme.colorScheme.surfaceContainerHighest,
                        child: const Center(
                            child: Icon(Icons.broken_image, size: 80)),
                      ),
                    )
                  : Container(
                      color: theme.colorScheme.surfaceContainerHighest,
                      child:
                          const Center(child: Icon(Icons.book, size: 80)),
                    ),
            ),
          ),
        ),
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  book.title,
                  style: theme.textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  book.authorsText,
                  style: theme.textTheme.titleMedium?.copyWith(
                    color: theme.colorScheme.primary,
                  ),
                ),
                const SizedBox(height: 16),
                _buildMetadataRow(theme, book),
                const SizedBox(height: 20),
                _buildLikeButton(context, ref, book, isLiked),
                const SizedBox(height: 8),
                _buildAddToListButton(context, ref, book),
                if (book.categories.isNotEmpty) ...[
                  const SizedBox(height: 20),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: book.categories
                        .map((c) => Chip(label: Text(c)))
                        .toList(),
                  ),
                ],
                if (book.description != null) ...[
                  const SizedBox(height: 20),
                  Text(
                    'Description',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    book.description!,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      height: 1.6,
                    ),
                  ),
                ],
                if (book.publisher != null ||
                    book.publishedDate != null) ...[
                  const SizedBox(height: 20),
                  Text(
                    'Publication Info',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  if (book.publisher != null)
                    _buildInfoRow(
                        Icons.business, 'Publisher', book.publisher!),
                  if (book.publishedDate != null)
                    _buildInfoRow(Icons.calendar_today, 'Published',
                        book.publishedDate!),
                ],
                ReviewSection(bookId: book.id),
                const SizedBox(height: 40),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildMetadataRow(ThemeData theme, Book book) {
    return Row(
      children: [
        if (book.averageRating != null) ...[
          const Icon(Icons.star, color: Color(0xFFFFC107), size: 20),
          const SizedBox(width: 4),
          Text(
            book.averageRating!.toStringAsFixed(1),
            style: theme.textTheme.bodyLarge?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          if (book.ratingsCount != null) ...[
            const SizedBox(width: 4),
            Text(
              '(${book.ratingsCount} reviews)',
              style: theme.textTheme.bodySmall,
            ),
          ],
          const SizedBox(width: 16),
        ],
        if (book.pageCount != null) ...[
          const Icon(Icons.menu_book, size: 20),
          const SizedBox(width: 4),
          Text(
            '${book.pageCount} pages',
            style: theme.textTheme.bodyMedium,
          ),
        ],
      ],
    );
  }

  Widget _buildLikeButton(
    BuildContext context,
    WidgetRef ref,
    Book book,
    bool isLiked,
  ) {
    return SizedBox(
      width: double.infinity,
      child: FilledButton.icon(
        onPressed: () {
          if (isLiked) {
            ref.read(likedBooksProvider.notifier).unlikeBook(book.id);
            showRemovedFromFavoritesSnackBar(context, book.title);
          } else {
            ref.read(likedBooksProvider.notifier).likeBook(book);
            showAddedToFavoritesSnackBar(context, book.title);
          }
        },
        icon: Icon(isLiked ? Icons.favorite : Icons.favorite_border),
        label: Text(isLiked ? 'Remove from Liked' : 'Like this Book'),
        style: FilledButton.styleFrom(
          backgroundColor:
              isLiked ? Theme.of(context).colorScheme.error : null,
          padding: const EdgeInsets.symmetric(vertical: 16),
        ),
      ),
    );
  }

  Widget _buildAddToListButton(BuildContext context, WidgetRef ref, Book book) {
    return SizedBox(
      width: double.infinity,
      child: OutlinedButton.icon(
        onPressed: () => _showAddToListDialog(context, ref, book.id),
        icon: const Icon(Icons.playlist_add),
        label: const Text('Add to List'),
        style: OutlinedButton.styleFrom(
          padding: const EdgeInsets.symmetric(vertical: 16),
        ),
      ),
    );
  }

  Future<void> _showAddToListDialog(BuildContext context, WidgetRef ref, String bookId) async {
    final listsAsync = ref.read(bookListsProvider);
    final lists = listsAsync.valueOrNull ?? [];

    if (lists.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Create a list first from the Book Lists screen')),
      );
      return;
    }

    final selectedListId = await showDialog<int>(
      context: context,
      builder: (context) => SimpleDialog(
        title: const Text('Add to List'),
        children: lists.map((list) {
          return SimpleDialogOption(
            onPressed: () => Navigator.pop(context, list['id'] as int),
            child: Text(list['name'] as String? ?? ''),
          );
        }).toList(),
      ),
    );

    if (selectedListId != null && context.mounted) {
      try {
        final api = ref.read(apiServiceProvider);
        await api.addBookToList(selectedListId, bookId);
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Book added to list')),
          );
        }
      } catch (e) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Failed: $e')),
          );
        }
      }
    }
  }

  Widget _buildInfoRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Icon(icon, size: 18),
          const SizedBox(width: 8),
          Text('$label: $value'),
        ],
      ),
    );
  }
}
