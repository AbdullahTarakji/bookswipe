import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/providers.dart';
import '../widgets/empty_state.dart';

/// Provides user search with follow/unfollow actions.
class UserSearchScreen extends ConsumerStatefulWidget {
  const UserSearchScreen({super.key});

  @override
  ConsumerState<UserSearchScreen> createState() => _UserSearchScreenState();
}

class _UserSearchScreenState extends ConsumerState<UserSearchScreen> {
  final _controller = TextEditingController();
  List<Map<String, dynamic>> _results = [];
  bool _loading = false;
  bool _searched = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _search() async {
    final query = _controller.text.trim();
    if (query.isEmpty) return;
    setState(() { _loading = true; _searched = true; });
    try {
      final api = ref.read(apiServiceProvider);
      final data = await api.searchUsers(query);
      final users = (data['users'] as List<dynamic>?) ?? [];
      if (mounted) {
        setState(() {
          _results = users.map((u) => u as Map<String, dynamic>).toList();
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _toggleFollow(int userId, bool isFollowing) async {
    final api = ref.read(apiServiceProvider);
    try {
      if (isFollowing) {
        await api.unfollowUser(userId);
      } else {
        await api.followUser(userId);
      }
      _search();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString())),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Find People')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: _controller,
              decoration: InputDecoration(
                hintText: 'Search by name or email...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.clear),
                  onPressed: () {
                    _controller.clear();
                    setState(() { _results = []; _searched = false; });
                  },
                ),
              ),
              textInputAction: TextInputAction.search,
              onSubmitted: (_) => _search(),
            ),
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _results.isEmpty
                    ? _searched
                        ? const EmptyState(
                            icon: Icons.person_search,
                            title: 'No users found',
                            subtitle: 'Try a different search term',
                          )
                        : const EmptyState(
                            icon: Icons.person_search,
                            title: 'Search for people',
                            subtitle: 'Find users to follow and see their book lists',
                          )
                    : ListView.builder(
                        itemCount: _results.length,
                        itemBuilder: (context, index) {
                          final user = _results[index];
                          final username = user['username'] as String? ?? '';
                          final userId = user['user_id'] as int;
                          final isFollowing = user['is_following'] as bool? ?? false;

                          return ListTile(
                            leading: CircleAvatar(
                              backgroundColor: theme.colorScheme.primaryContainer,
                              child: Icon(
                                Icons.person,
                                color: theme.colorScheme.onPrimaryContainer,
                                size: 20,
                              ),
                            ),
                            title: Text(username),
                            trailing: TextButton(
                              onPressed: () => _toggleFollow(userId, isFollowing),
                              child: Text(isFollowing ? 'Unfollow' : 'Follow'),
                            ),
                            onTap: () => context.push('/social/profile/$userId'),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }
}
