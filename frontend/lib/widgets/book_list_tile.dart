import 'package:flutter/material.dart';
import '../models/book.dart';

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
    final tile = ListTile(
      onTap: onTap,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      leading: Hero(
        tag: 'book-cover-${book.id}',
        child: ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: SizedBox(
            width: 50,
            height: 70,
            child: book.thumbnailUrl != null
                ? Image.network(
                    book.highResThumbnail,
                    fit: BoxFit.cover,
                    errorBuilder: (_, _, _) => Container(
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
      title: Text(
        book.title,
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
      ),
      subtitle: Text(
        book.authorsText,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
      trailing: book.averageRating != null
          ? Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.star, size: 16, color: Color(0xFFFFC107)),
                const SizedBox(width: 4),
                Text(book.averageRating!.toStringAsFixed(1)),
              ],
            )
          : null,
    );

    if (onDismiss != null) {
      return Dismissible(
        key: ValueKey(book.id),
        direction: DismissDirection.endToStart,
        background: Container(
          alignment: Alignment.centerRight,
          padding: const EdgeInsets.only(right: 20),
          color: theme.colorScheme.error,
          child: const Icon(Icons.delete, color: Colors.white),
        ),
        onDismissed: (_) => onDismiss!(),
        child: tile,
      );
    }

    return tile;
  }
}
