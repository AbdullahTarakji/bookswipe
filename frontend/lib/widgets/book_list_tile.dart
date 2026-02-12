import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import '../models/book.dart';
import '../theme/app_theme.dart';

/// Tinder-style "match" list tile for the Liked Books screen.
class BookListTile extends StatelessWidget {
  final Book book;
  final VoidCallback? onTap;
  final VoidCallback? onDismiss;

  const BookListTile({
    super.key,
    required this.book,
    this.onTap,
    this.onDismiss,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final tile = InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        child: Row(
          children: [
            // Rounded cover thumbnail
            Hero(
              tag: 'book-cover-${book.id}',
              child: ClipRRect(
                borderRadius: BorderRadius.circular(10),
                child: SizedBox(
                  width: 56,
                  height: 80,
                  child: book.thumbnailUrl != null
                      ? CachedNetworkImage(
                          imageUrl: book.highResThumbnail,
                          fit: BoxFit.cover,
                          errorWidget: (ctx, url, err) => Container(
                            color: theme.colorScheme.surfaceContainerHighest,
                            child: const Icon(Icons.broken_image, size: 24),
                          ),
                        )
                      : Container(
                          color: theme.colorScheme.surfaceContainerHighest,
                          child: const Icon(Icons.book, size: 24),
                        ),
                ),
              ),
            ),
            const SizedBox(width: 14),
            // Title + author
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    book.title,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    book.authorsText,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: theme.textTheme.bodySmall?.copyWith(color: AppTheme.textSecondary),
                  ),
                ],
              ),
            ),
            // Rating badge
            if (book.averageRating != null) ...[
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: AppTheme.rewindYellow.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.star_rounded, size: 14, color: AppTheme.rewindYellow),
                    const SizedBox(width: 3),
                    Text(
                      book.averageRating!.toStringAsFixed(1),
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.rewindYellow,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );

    if (onDismiss != null) {
      return Dismissible(
        key: ValueKey(book.id),
        direction: DismissDirection.endToStart,
        background: Container(
          alignment: Alignment.centerRight,
          padding: const EdgeInsets.only(right: 24),
          color: AppTheme.nopeRed,
          child: const Icon(Icons.delete_outline_rounded, color: Colors.white, size: 28),
        ),
        onDismissed: (_) => onDismiss!(),
        child: tile,
      );
    }

    return tile;
  }
}
