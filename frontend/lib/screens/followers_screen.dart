import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/providers.dart';
import '../widgets/empty_state.dart';

/// Displays the user's followers and following lists in tabs.
class FollowersScreen extends ConsumerStatefulWidget {
  const FollowersScreen({super.key});

  @override
  ConsumerState<FollowersScreen> createState() => _FollowersScreenState();
}

class _FollowersScreenState extends ConsumerState<FollowersScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<Map<String, dynamic>> _followers = [];
  List<Map<String, dynamic>> _following = [];
  bool _loadingFollowers = true;
  bool _loadingFollowing = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    final api = ref.read(apiServiceProvider);
    try {
      final followersData = await api.getFollowers();
      if (mounted) {
        setState(() {
          _followers = ((followersData['users'] as List<dynamic>?) ?? [])
              .map((u) => u as Map<String, dynamic>)
              .toList();
          _loadingFollowers = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _loadingFollowers = false);
    }
    try {
      final followingData = await api.getFollowing();
      if (mounted) {
        setState(() {
          _following = ((followingData['users'] as List<dynamic>?) ?? [])
              .map((u) => u as Map<String, dynamic>)
              .toList();
          _loadingFollowing = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _loadingFollowing = false);
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
      _loadData();
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
      appBar: AppBar(
        title: const Text('Connections'),
        bottom: TabBar(
          controller: _tabController,
          tabs: [
            Tab(text: 'Followers (${_followers.length})'),
            Tab(text: 'Following (${_following.length})'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildUserList(_followers, _loadingFollowers, 'No followers yet', theme),
          _buildUserList(_following, _loadingFollowing, 'Not following anyone', theme),
        ],
      ),
    );
  }

  Widget _buildUserList(
    List<Map<String, dynamic>> users,
    bool loading,
    String emptyMessage,
    ThemeData theme,
  ) {
    if (loading) return const Center(child: CircularProgressIndicator());
    if (users.isEmpty) {
      return EmptyState(icon: Icons.people_outline, title: emptyMessage, subtitle: 'Find people to connect with');
    }
    return RefreshIndicator(
      onRefresh: _loadData,
      child: ListView.builder(
        itemCount: users.length,
        itemBuilder: (context, index) {
          final user = users[index];
          final username = user['username'] as String? ?? '';
          final userId = user['user_id'] as int;
          final isFollowing = user['is_following'] as bool? ?? false;

          return ListTile(
            leading: CircleAvatar(
              backgroundColor: theme.colorScheme.primaryContainer,
              child: Icon(Icons.person, color: theme.colorScheme.onPrimaryContainer, size: 20),
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
    );
  }
}
