import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/social_providers.dart';
import '../widgets/empty_state.dart';
import '../widgets/error_view.dart';
import '../widgets/responsive_container.dart';
import '../widgets/shimmer_loading.dart';

/// Displays the user's book lists and public lists with tabs.
class BookListsScreen extends ConsumerWidget {
  const BookListsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Book Lists'),
          bottom: const TabBar(
            tabs: [
              Tab(text: 'My Lists'),
              Tab(text: 'Discover'),
            ],
          ),
        ),
        floatingActionButton: FloatingActionButton(
          onPressed: () => _showCreateDialog(context, ref),
          child: const Icon(Icons.add),
        ),
        body: const TabBarView(
          children: [
            _MyListsTab(),
            _PublicListsTab(),
          ],
        ),
      ),
    );
  }

  Future<void> _showCreateDialog(BuildContext context, WidgetRef ref) async {
    final nameController = TextEditingController();
    final descController = TextEditingController();
    var isPublic = true;

    final result = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Create Book List'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: nameController,
                  decoration: const InputDecoration(
                    labelText: 'List Name',
                    hintText: 'e.g. Summer Reading',
                  ),
                  autofocus: true,
                  maxLength: 200,
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: descController,
                  decoration: const InputDecoration(
                    labelText: 'Description (optional)',
                  ),
                  maxLines: 2,
                  maxLength: 1000,
                ),
                const SizedBox(height: 8),
                SwitchListTile(
                  title: const Text('Public'),
                  value: isPublic,
                  onChanged: (v) => setDialogState(() => isPublic = v),
                  contentPadding: EdgeInsets.zero,
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
            FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Create')),
          ],
        ),
      ),
    );

    if (result == true && nameController.text.isNotEmpty) {
      await ref.read(bookListsProvider.notifier).createList(
            name: nameController.text,
            description: descController.text,
            isPublic: isPublic,
          );
    }
    nameController.dispose();
    descController.dispose();
  }
}

class _MyListsTab extends ConsumerWidget {
  const _MyListsTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final listsState = ref.watch(bookListsProvider);
    final theme = Theme.of(context);

    return listsState.when(
      loading: () => const FavoritesShimmer(),
      error: (error, _) => ErrorView(
        message: error.toString(),
        onRetry: () => ref.read(bookListsProvider.notifier).refresh(),
      ),
      data: (lists) {
        if (lists.isEmpty) {
          return const EmptyState(
            icon: Icons.list,
            title: 'No book lists yet',
            subtitle: 'Create a list to organize your reading',
          );
        }
        final isTablet = ResponsiveContainer.isTablet(context);
        return RefreshIndicator(
          onRefresh: () => ref.read(bookListsProvider.notifier).refresh(),
          child: isTablet
              ? GridView.builder(
                  padding: const EdgeInsets.all(8),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    childAspectRatio: 3.5,
                    crossAxisSpacing: 8,
                    mainAxisSpacing: 8,
                  ),
                  itemCount: lists.length,
                  itemBuilder: (context, index) {
                    final list = lists[index];
                    return _BookListTile(list: list, theme: theme, canDelete: true);
                  },
                )
              : ListView.builder(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  itemCount: lists.length,
                  itemBuilder: (context, index) {
                    final list = lists[index];
                    return _BookListTile(list: list, theme: theme, canDelete: true);
                  },
                ),
        );
      },
    );
  }
}

class _PublicListsTab extends ConsumerWidget {
  const _PublicListsTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final listsState = ref.watch(publicListsProvider);
    final theme = Theme.of(context);

    return listsState.when(
      loading: () => const FavoritesShimmer(),
      error: (error, _) => ErrorView(
        message: error.toString(),
        onRetry: () => ref.read(publicListsProvider.notifier).refresh(),
      ),
      data: (lists) {
        if (lists.isEmpty) {
          return const EmptyState(
            icon: Icons.explore,
            title: 'No public lists yet',
            subtitle: 'Public lists from other users will appear here',
          );
        }
        final isTablet = ResponsiveContainer.isTablet(context);
        return RefreshIndicator(
          onRefresh: () => ref.read(publicListsProvider.notifier).refresh(),
          child: isTablet
              ? GridView.builder(
                  padding: const EdgeInsets.all(8),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    childAspectRatio: 3.5,
                    crossAxisSpacing: 8,
                    mainAxisSpacing: 8,
                  ),
                  itemCount: lists.length,
                  itemBuilder: (context, index) {
                    final list = lists[index];
                    return _BookListTile(list: list, theme: theme, canDelete: false);
                  },
                )
              : ListView.builder(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  itemCount: lists.length,
                  itemBuilder: (context, index) {
                    final list = lists[index];
                    return _BookListTile(list: list, theme: theme, canDelete: false);
                  },
                ),
        );
      },
    );
  }
}

class _BookListTile extends ConsumerWidget {
  final Map<String, dynamic> list;
  final ThemeData theme;
  final bool canDelete;

  const _BookListTile({required this.list, required this.theme, required this.canDelete});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final name = list['name'] as String? ?? '';
    final description = list['description'] as String? ?? '';
    final itemCount = list['item_count'] as int? ?? 0;
    final isPublic = list['is_public'] as bool? ?? true;
    final listId = list['id'] as int;
    final ownerUsername = list['owner_username'] as String? ?? '';

    Widget tile = ListTile(
      leading: CircleAvatar(
        backgroundColor: theme.colorScheme.secondaryContainer,
        child: Icon(
          isPublic ? Icons.public : Icons.lock,
          color: theme.colorScheme.onSecondaryContainer,
          size: 20,
        ),
      ),
      title: Text(name),
      subtitle: Text(
        canDelete
            ? (description.isNotEmpty ? description : '$itemCount books')
            : 'by $ownerUsername · $itemCount books',
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
      trailing: Text('$itemCount', style: theme.textTheme.bodySmall),
      onTap: () => context.push('/social/lists/$listId'),
    );

    if (!canDelete) return tile;

    return Dismissible(
      key: ValueKey(listId),
      direction: DismissDirection.endToStart,
      background: Container(
        color: theme.colorScheme.error,
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 16),
        child: Icon(Icons.delete, color: theme.colorScheme.onError),
      ),
      confirmDismiss: (_) async {
        return await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('Delete List?'),
            content: Text('Delete "$name" and all its items?'),
            actions: [
              TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
              FilledButton(
                onPressed: () => Navigator.pop(context, true),
                style: FilledButton.styleFrom(backgroundColor: theme.colorScheme.error),
                child: const Text('Delete'),
              ),
            ],
          ),
        );
      },
      onDismissed: (_) {
        ref.read(bookListsProvider.notifier).deleteList(listId);
      },
      child: tile,
    );
  }
}
