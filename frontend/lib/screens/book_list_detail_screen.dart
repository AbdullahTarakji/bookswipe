import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/providers.dart';
import '../widgets/empty_state.dart';
import '../widgets/error_view.dart';
import '../widgets/shimmer_loading.dart';

/// Displays a book list's items with add/remove functionality.
class BookListDetailScreen extends ConsumerStatefulWidget {
  final int listId;

  const BookListDetailScreen({super.key, required this.listId});

  @override
  ConsumerState<BookListDetailScreen> createState() => _BookListDetailScreenState();
}

class _BookListDetailScreenState extends ConsumerState<BookListDetailScreen> {
  Map<String, dynamic>? _listData;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadList();
  }

  Future<void> _loadList() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final api = ref.read(apiServiceProvider);
      final data = await api.getBookList(widget.listId);
      if (mounted) setState(() { _listData = data; _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (_loading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Book List')),
        body: const FavoritesShimmer(),
      );
    }

    if (_error != null || _listData == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Book List')),
        body: ErrorView(message: _error ?? 'Failed to load list', onRetry: _loadList),
      );
    }

    final data = _listData!;
    final name = data['name'] as String? ?? '';
    final description = data['description'] as String? ?? '';
    final items = (data['items'] as List<dynamic>?) ?? [];

    return Scaffold(
      appBar: AppBar(title: Text(name)),
      body: RefreshIndicator(
        onRefresh: _loadList,
        child: items.isEmpty
            ? ListView(
                children: [
                  if (description.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.all(16),
                      child: Text(description, style: theme.textTheme.bodyMedium),
                    ),
                  const SizedBox(height: 60),
                  const EmptyState(
                    icon: Icons.menu_book,
                    title: 'No books in this list',
                    subtitle: 'Add books from your liked books',
                  ),
                ],
              )
            : ListView.builder(
                padding: const EdgeInsets.symmetric(vertical: 8),
                itemCount: items.length + (description.isNotEmpty ? 1 : 0),
                itemBuilder: (context, index) {
                  if (description.isNotEmpty && index == 0) {
                    return Padding(
                      padding: const EdgeInsets.all(16),
                      child: Text(description, style: theme.textTheme.bodyMedium),
                    );
                  }
                  final itemIndex = description.isNotEmpty ? index - 1 : index;
                  final item = items[itemIndex] as Map<String, dynamic>;
                  return _BookListItemTile(
                    item: item,
                    listId: widget.listId,
                    onRemoved: _loadList,
                    theme: theme,
                  );
                },
              ),
      ),
    );
  }
}

class _BookListItemTile extends ConsumerWidget {
  final Map<String, dynamic> item;
  final int listId;
  final VoidCallback onRemoved;
  final ThemeData theme;

  const _BookListItemTile({
    required this.item,
    required this.listId,
    required this.onRemoved,
    required this.theme,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bookId = item['book_id'] as String? ?? '';
    final note = item['note'] as String? ?? '';

    return ListTile(
      leading: CircleAvatar(
        backgroundColor: theme.colorScheme.tertiaryContainer,
        child: Icon(Icons.book, color: theme.colorScheme.onTertiaryContainer, size: 20),
      ),
      title: Text(bookId, maxLines: 1, overflow: TextOverflow.ellipsis),
      subtitle: note.isNotEmpty ? Text(note, maxLines: 1, overflow: TextOverflow.ellipsis) : null,
      trailing: IconButton(
        icon: const Icon(Icons.remove_circle_outline),
        onPressed: () async {
          try {
            final api = ref.read(apiServiceProvider);
            await api.removeBookFromList(listId, bookId);
            onRemoved();
          } catch (e) {
            if (context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text(e.toString())),
              );
            }
          }
        },
      ),
      onTap: () => context.push('/book/$bookId'),
    );
  }
}
