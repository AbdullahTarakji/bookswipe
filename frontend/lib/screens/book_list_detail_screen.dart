import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/providers.dart';
import '../widgets/empty_state.dart';
import '../widgets/error_view.dart';
import '../widgets/shimmer_loading.dart';

/// Displays a book list's items with add/remove and reorder functionality.
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
  bool _reordering = false;

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

  bool get _isOwner {
    // Check if current user owns this list
    final auth = ref.read(authStateProvider);
    final userId = auth.valueOrNull?.id;
    return userId != null && _listData?['user_id'].toString() == userId;
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
    final items = List<Map<String, dynamic>>.from(
      (data['items'] as List<dynamic>?)?.map((e) => e as Map<String, dynamic>) ?? [],
    );
    final ownerUsername = data['owner_username'] as String? ?? '';

    return Scaffold(
      appBar: AppBar(
        title: Text(name),
        actions: [
          if (_isOwner && items.length > 1)
            IconButton(
              icon: Icon(_reordering ? Icons.check : Icons.reorder),
              onPressed: () => setState(() => _reordering = !_reordering),
              tooltip: _reordering ? 'Done reordering' : 'Reorder',
            ),
        ],
      ),
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
                  if (!_isOwner && ownerUsername.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: Text('by $ownerUsername', style: theme.textTheme.bodySmall),
                    ),
                  const SizedBox(height: 60),
                  const EmptyState(
                    icon: Icons.menu_book,
                    title: 'No books in this list',
                    subtitle: 'Add books from your liked books',
                  ),
                ],
              )
            : _reordering
                ? _buildReorderableList(items, description, theme)
                : _buildItemList(items, description, ownerUsername, theme),
      ),
    );
  }

  Widget _buildItemList(
    List<Map<String, dynamic>> items,
    String description,
    String ownerUsername,
    ThemeData theme,
  ) {
    final headerCount = (description.isNotEmpty ? 1 : 0) + (!_isOwner && ownerUsername.isNotEmpty ? 1 : 0);
    return ListView.builder(
      padding: const EdgeInsets.symmetric(vertical: 8),
      itemCount: items.length + headerCount,
      itemBuilder: (context, index) {
        int offset = 0;
        if (description.isNotEmpty && index == 0) {
          return Padding(
            padding: const EdgeInsets.all(16),
            child: Text(description, style: theme.textTheme.bodyMedium),
          );
        }
        if (description.isNotEmpty) offset++;
        if (!_isOwner && ownerUsername.isNotEmpty && index == offset) {
          return Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: Text('by $ownerUsername', style: theme.textTheme.bodySmall),
          );
        }
        if (!_isOwner && ownerUsername.isNotEmpty) offset++;
        final itemIndex = index - offset;
        final item = items[itemIndex];
        return _BookListItemTile(
          item: item,
          listId: widget.listId,
          onRemoved: _loadList,
          theme: theme,
          canRemove: _isOwner,
        );
      },
    );
  }

  Widget _buildReorderableList(
    List<Map<String, dynamic>> items,
    String description,
    ThemeData theme,
  ) {
    return ReorderableListView.builder(
      padding: const EdgeInsets.symmetric(vertical: 8),
      itemCount: items.length,
      onReorder: (oldIndex, newIndex) async {
        if (newIndex > oldIndex) newIndex--;
        setState(() {
          final item = items.removeAt(oldIndex);
          items.insert(newIndex, item);
          _listData!['items'] = items;
        });
        // Persist new order
        try {
          final api = ref.read(apiServiceProvider);
          final bookIds = items.map((i) => i['book_id'] as String).toList();
          await api.reorderBookList(widget.listId, bookIds);
        } catch (e) {
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Failed to reorder: $e')),
            );
            _loadList();
          }
        }
      },
      itemBuilder: (context, index) {
        final item = items[index];
        final bookId = item['book_id'] as String? ?? '';
        final note = item['note'] as String? ?? '';
        return ListTile(
          key: ValueKey(bookId),
          leading: const Icon(Icons.drag_handle),
          title: Text(bookId, maxLines: 1, overflow: TextOverflow.ellipsis),
          subtitle: note.isNotEmpty ? Text(note, maxLines: 1, overflow: TextOverflow.ellipsis) : null,
        );
      },
    );
  }
}

class _BookListItemTile extends ConsumerWidget {
  final Map<String, dynamic> item;
  final int listId;
  final VoidCallback onRemoved;
  final ThemeData theme;
  final bool canRemove;

  const _BookListItemTile({
    required this.item,
    required this.listId,
    required this.onRemoved,
    required this.theme,
    this.canRemove = true,
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
      trailing: canRemove
          ? IconButton(
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
            )
          : null,
      onTap: () => context.push('/book/$bookId'),
    );
  }
}
