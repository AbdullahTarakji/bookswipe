import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/providers.dart';

class AdminUsersScreen extends ConsumerStatefulWidget {
  const AdminUsersScreen({super.key});

  @override
  ConsumerState<AdminUsersScreen> createState() => _AdminUsersScreenState();
}

class _AdminUsersScreenState extends ConsumerState<AdminUsersScreen> {
  final TextEditingController _searchController = TextEditingController();
  String? _roleFilter;
  bool? _bannedFilter;

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _applyFilters() {
    ref.read(adminUsersProvider.notifier).setFilters(
          search: _searchController.text.isEmpty ? null : _searchController.text,
          role: _roleFilter,
          isBanned: _bannedFilter,
        );
  }

  @override
  Widget build(BuildContext context) {
    final usersAsync = ref.watch(adminUsersProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('User Management'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(adminUsersProvider.notifier).refresh(),
          ),
        ],
      ),
      body: Column(
        children: [
          // Search & filter bar
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                TextField(
                  controller: _searchController,
                  decoration: InputDecoration(
                    hintText: 'Search by email...',
                    prefixIcon: const Icon(Icons.search),
                    suffixIcon: _searchController.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear),
                            onPressed: () {
                              _searchController.clear();
                              _applyFilters();
                            },
                          )
                        : null,
                  ),
                  onSubmitted: (_) => _applyFilters(),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                      child: DropdownButtonFormField<String?>(
                        initialValue: _roleFilter,
                        decoration: const InputDecoration(
                          labelText: 'Role',
                          contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        ),
                        items: const [
                          DropdownMenuItem(value: null, child: Text('All')),
                          DropdownMenuItem(value: 'admin', child: Text('Admin')),
                          DropdownMenuItem(value: 'user', child: Text('User')),
                        ],
                        onChanged: (v) {
                          setState(() => _roleFilter = v);
                          _applyFilters();
                        },
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: DropdownButtonFormField<bool?>(
                        initialValue: _bannedFilter,
                        decoration: const InputDecoration(
                          labelText: 'Status',
                          contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        ),
                        items: const [
                          DropdownMenuItem(value: null, child: Text('All')),
                          DropdownMenuItem(value: true, child: Text('Banned')),
                          DropdownMenuItem(value: false, child: Text('Active')),
                        ],
                        onChanged: (v) {
                          setState(() => _bannedFilter = v);
                          _applyFilters();
                        },
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          // User list
          Expanded(
            child: usersAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, _) => Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text('Error: $error'),
                    const SizedBox(height: 16),
                    FilledButton(
                      onPressed: () => ref.read(adminUsersProvider.notifier).refresh(),
                      child: const Text('Retry'),
                    ),
                  ],
                ),
              ),
              data: (data) {
                final users = (data['users'] as List<dynamic>?) ?? [];
                final total = data['total'] as int? ?? 0;
                final page = data['page'] as int? ?? 1;
                final pageSize = data['page_size'] as int? ?? 20;

                if (users.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.people_outline, size: 64, color: theme.colorScheme.onSurfaceVariant),
                        const SizedBox(height: 16),
                        Text('No users found', style: theme.textTheme.titleMedium),
                      ],
                    ),
                  );
                }

                return Column(
                  children: [
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: Text(
                        '$total user${total == 1 ? '' : 's'} found',
                        style: theme.textTheme.bodySmall,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Expanded(
                      child: ListView.builder(
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        itemCount: users.length,
                        itemBuilder: (context, index) => _UserCard(
                          user: users[index] as Map<String, dynamic>,
                          onAction: () => ref.read(adminUsersProvider.notifier).refresh(),
                        ),
                      ),
                    ),
                    // Pagination
                    if (total > pageSize)
                      Padding(
                        padding: const EdgeInsets.all(16),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            IconButton(
                              onPressed: page > 1
                                  ? () => ref.read(adminUsersProvider.notifier).setPage(page - 1)
                                  : null,
                              icon: const Icon(Icons.chevron_left),
                            ),
                            Text('Page $page of ${(total / pageSize).ceil()}'),
                            IconButton(
                              onPressed: page * pageSize < total
                                  ? () => ref.read(adminUsersProvider.notifier).setPage(page + 1)
                                  : null,
                              icon: const Icon(Icons.chevron_right),
                            ),
                          ],
                        ),
                      ),
                  ],
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _UserCard extends ConsumerWidget {
  final Map<String, dynamic> user;
  final VoidCallback onAction;

  const _UserCard({required this.user, required this.onAction});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final email = user['email'] as String? ?? '';
    final role = user['role'] as String? ?? 'user';
    final isBanned = user['is_banned'] as bool? ?? false;
    final banReason = user['ban_reason'] as String?;
    final createdAt = user['created_at'] as String? ?? '';
    final userId = user['id'] as int? ?? 0;
    final authProvider = user['auth_provider'] as String? ?? 'email';

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => _showUserDetailDialog(context, ref),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  CircleAvatar(
                    radius: 20,
                    backgroundColor: role == 'admin'
                        ? Colors.purple.withValues(alpha: 0.2)
                        : theme.colorScheme.primaryContainer,
                    child: Icon(
                      role == 'admin' ? Icons.admin_panel_settings : Icons.person,
                      size: 20,
                      color: role == 'admin' ? Colors.purple : theme.colorScheme.onPrimaryContainer,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          email,
                          style: theme.textTheme.titleSmall,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        Text(
                          'ID: $userId | $authProvider | ${createdAt.isNotEmpty ? createdAt.substring(0, 10) : ''}',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.onSurfaceVariant,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                children: [
                  _buildChip(role == 'admin' ? 'Admin' : 'User',
                      role == 'admin' ? Colors.purple : Colors.blue),
                  if (isBanned)
                    _buildChip('Banned', Colors.red),
                  if (banReason != null && banReason.isNotEmpty)
                    _buildChip(banReason, Colors.orange),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildChip(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        label,
        style: TextStyle(color: color, fontSize: 12),
      ),
    );
  }

  void _showUserDetailDialog(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final email = user['email'] as String? ?? '';
    final role = user['role'] as String? ?? 'user';
    final isBanned = user['is_banned'] as bool? ?? false;
    final userId = user['id'] as int? ?? 0;
    final currentUser = ref.read(authStateProvider).valueOrNull;
    final isSelf = currentUser?.id == userId.toString();
    final isTargetAdmin = role == 'admin';

    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(email, style: theme.textTheme.titleMedium),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Role: $role'),
            Text('Banned: ${isBanned ? 'Yes' : 'No'}'),
            if (user['ban_reason'] != null)
              Text('Reason: ${user['ban_reason']}'),
            Text('Provider: ${user['auth_provider'] ?? 'email'}'),
            Text('Created: ${user['created_at'] ?? ''}'),
          ],
        ),
        actions: [
          if (!isSelf && !isTargetAdmin)
            TextButton.icon(
              icon: Icon(isBanned ? Icons.check_circle : Icons.block),
              label: Text(isBanned ? 'Unban' : 'Ban'),
              onPressed: () async {
                Navigator.of(dialogContext).pop();
                await _toggleBan(context, ref, userId, isBanned);
              },
            ),
          if (!isSelf)
            TextButton.icon(
              icon: const Icon(Icons.swap_horiz),
              label: Text(role == 'admin' ? 'Make User' : 'Make Admin'),
              onPressed: () async {
                Navigator.of(dialogContext).pop();
                await _changeRole(context, ref, userId, role == 'admin' ? 'user' : 'admin');
              },
            ),
          if (!isSelf && !isTargetAdmin)
            TextButton.icon(
              icon: const Icon(Icons.delete_forever),
              label: const Text('Delete'),
              style: TextButton.styleFrom(foregroundColor: Colors.red),
              onPressed: () {
                Navigator.of(dialogContext).pop();
                _confirmDelete(context, ref, userId, email);
              },
            ),
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  Future<void> _toggleBan(BuildContext context, WidgetRef ref, int userId, bool currentlyBanned) async {
    try {
      final api = ref.read(apiServiceProvider);
      String? reason;
      if (!currentlyBanned && context.mounted) {
        reason = await _showReasonDialog(context);
        if (reason == null) return; // User cancelled
      }
      await api.toggleBanUser(userId, reason: reason);
      onAction();
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(currentlyBanned ? 'User unbanned' : 'User banned')),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: ${_formatError(e)}')),
        );
      }
    }
  }

  Future<String?> _showReasonDialog(BuildContext context) async {
    final controller = TextEditingController();
    return showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Ban Reason'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(hintText: 'Optional reason...'),
          maxLines: 2,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(null),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(controller.text),
            child: const Text('Ban'),
          ),
        ],
      ),
    );
  }

  Future<void> _changeRole(BuildContext context, WidgetRef ref, int userId, String newRole) async {
    try {
      final api = ref.read(apiServiceProvider);
      await api.updateUserRole(userId, newRole);
      onAction();
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Role changed to $newRole')),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: ${_formatError(e)}')),
        );
      }
    }
  }

  void _confirmDelete(BuildContext context, WidgetRef ref, int userId, String email) {
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Delete User'),
        content: Text('Permanently delete $email? This cannot be undone.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () async {
              Navigator.of(dialogContext).pop();
              try {
                final api = ref.read(apiServiceProvider);
                await api.deleteUser(userId);
                onAction();
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('User deleted')),
                  );
                }
              } catch (e) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Error: ${_formatError(e)}')),
                  );
                }
              }
            },
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }

  String _formatError(Object e) {
    if (e is Exception) {
      return e.toString().replaceFirst('Exception: ', '');
    }
    return e.toString();
  }
}
