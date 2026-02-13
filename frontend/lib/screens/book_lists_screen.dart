import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/social_providers.dart';
import '../widgets/empty_state.dart';
import '../widgets/error_view.dart';
import '../widgets/shimmer_loading.dart';

/// Displays the user's book lists with create/delete functionality.
class BookListsScreen extends ConsumerWidget {
  const BookListsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final listsState = ref.watch(bookListsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Book Lists')),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showCreateDialog(context, ref),
        child: const Icon(Icons.add),
      ),
      body: listsState.when(
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
          return RefreshIndicator(
            onRefresh: () => ref.read(bookListsProvider.notifier).refresh(),
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(vertical: 8),
              itemCount: lists.length,
              itemBuilder: (context, index) {
                final list = lists[index];
                return _BookListTile(list: list, theme: theme);
              },
            ),
          );
        },
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

class _BookListTile extends ConsumerWidget {
  final Map<String, dynamic> list;
  final ThemeData theme;

  const _BookListTile({required this.list, required this.theme});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final name = list['name'] as String? ?? '';
    final description = list['description'] as String? ?? '';
    final itemCount = list['item_count'] as int? ?? 0;
    final isPublic = list['is_public'] as bool? ?? true;
    final listId = list['id'] as int;

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
      child: ListTile(
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
          description.isNotEmpty ? description : '$itemCount books',
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        trailing: Text('$itemCount', style: theme.textTheme.bodySmall),
        onTap: () => context.push('/social/lists/$listId'),
      ),
    );
  }
}
