import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/providers.dart';
import '../widgets/error_view.dart';
import '../widgets/shimmer_loading.dart';

/// Displays the user's social profile with follower/following counts and bio.
class SocialProfileScreen extends ConsumerStatefulWidget {
  final int? userId;

  const SocialProfileScreen({super.key, this.userId});

  @override
  ConsumerState<SocialProfileScreen> createState() => _SocialProfileScreenState();
}

class _SocialProfileScreenState extends ConsumerState<SocialProfileScreen> {
  Map<String, dynamic>? _profile;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final api = ref.read(apiServiceProvider);
      final data = widget.userId != null
          ? await api.getUserProfile(widget.userId!)
          : await api.getSocialProfile();
      if (mounted) {
        setState(() {
          _profile = data;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _loading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isOwnProfile = widget.userId == null;

    if (_loading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Profile')),
        body: const HomeShimmer(),
      );
    }

    if (_error != null || _profile == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Profile')),
        body: ErrorView(
          message: _error ?? 'Failed to load profile',
          onRetry: _loadProfile,
        ),
      );
    }

    final profile = _profile!;
    final username = profile['username'] as String? ?? '';
    final bio = profile['bio'] as String? ?? '';
    final followersCount = profile['followers_count'] as int? ?? 0;
    final followingCount = profile['following_count'] as int? ?? 0;
    final booksLiked = profile['books_liked_count'] as int? ?? 0;
    final isFollowing = profile['is_following'] as bool? ?? false;
    final readingGoal = profile['reading_goal'] as int?;

    return Scaffold(
      appBar: AppBar(
        title: Text(username),
        actions: [
          IconButton(
            icon: const Icon(Icons.share),
            tooltip: 'Share',
            onPressed: () {
              final uid = widget.userId ?? profile['user_id'] as int?;
              if (uid != null) {
                ref.read(shareServiceProvider).shareUser(context, uid);
              }
            },
          ),
          if (isOwnProfile)
            IconButton(
              icon: const Icon(Icons.edit),
              onPressed: () => _showEditDialog(context, profile),
            ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadProfile,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            const SizedBox(height: 10),
            CircleAvatar(
              radius: 50,
              backgroundColor: theme.colorScheme.primaryContainer,
              child: Icon(Icons.person, size: 50, color: theme.colorScheme.onPrimaryContainer),
            ),
            const SizedBox(height: 16),
            Text(
              username,
              style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
            if (bio.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(bio, style: theme.textTheme.bodyMedium, textAlign: TextAlign.center),
            ],
            const SizedBox(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _StatColumn(count: followersCount, label: 'Followers'),
                _StatColumn(count: followingCount, label: 'Following'),
                _StatColumn(count: booksLiked, label: 'Books Liked'),
              ],
            ),
            if (readingGoal != null) ...[
              const SizedBox(height: 16),
              Card(
                child: ListTile(
                  leading: const Icon(Icons.flag),
                  title: Text('Reading Goal: $readingGoal books'),
                  subtitle: LinearProgressIndicator(
                    value: booksLiked / readingGoal.clamp(1, 1000),
                    backgroundColor: theme.colorScheme.surfaceContainerHighest,
                  ),
                ),
              ),
            ],
            if (!isOwnProfile) ...[
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: () => _toggleFollow(profile),
                icon: Icon(isFollowing ? Icons.person_remove : Icons.person_add),
                label: Text(isFollowing ? 'Unfollow' : 'Follow'),
                style: isFollowing
                    ? FilledButton.styleFrom(
                        backgroundColor: theme.colorScheme.surfaceContainerHighest,
                        foregroundColor: theme.colorScheme.onSurface,
                      )
                    : null,
              ),
            ],
            const SizedBox(height: 24),
            if (isOwnProfile) ...[
              Card(
                child: Column(
                  children: [
                    ListTile(
                      leading: const Icon(Icons.people),
                      title: const Text('Followers & Following'),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => context.push('/social/followers'),
                    ),
                    const Divider(height: 1),
                    ListTile(
                      leading: const Icon(Icons.rss_feed),
                      title: const Text('Activity Feed'),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => context.push('/social/feed'),
                    ),
                    const Divider(height: 1),
                    ListTile(
                      leading: const Icon(Icons.list),
                      title: const Text('Book Lists'),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => context.push('/social/lists'),
                    ),
                    const Divider(height: 1),
                    ListTile(
                      leading: const Icon(Icons.search),
                      title: const Text('Find People'),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => context.push('/social/search'),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Future<void> _toggleFollow(Map<String, dynamic> profile) async {
    final api = ref.read(apiServiceProvider);
    final userId = profile['user_id'] as int;
    final isFollowing = profile['is_following'] as bool? ?? false;
    try {
      if (isFollowing) {
        await api.unfollowUser(userId);
      } else {
        await api.followUser(userId);
      }
      _loadProfile();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString())),
        );
      }
    }
  }

  Future<void> _showEditDialog(BuildContext dialogContext, Map<String, dynamic> profile) async {
    final messenger = ScaffoldMessenger.of(dialogContext);
    final bioController = TextEditingController(text: profile['bio'] as String? ?? '');
    final goalController = TextEditingController(
      text: (profile['reading_goal'] as int?)?.toString() ?? '',
    );
    var isPublic = profile['is_public'] as bool? ?? true;

    final result = await showDialog<bool>(
      context: dialogContext,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Edit Profile'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: bioController,
                  decoration: const InputDecoration(
                    labelText: 'Bio',
                    hintText: 'Tell us about yourself...',
                  ),
                  maxLines: 3,
                  maxLength: 500,
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: goalController,
                  decoration: const InputDecoration(
                    labelText: 'Reading Goal (books/year)',
                    hintText: 'e.g. 24',
                  ),
                  keyboardType: TextInputType.number,
                ),
                const SizedBox(height: 16),
                SwitchListTile(
                  title: const Text('Public Profile'),
                  subtitle: const Text('Let others find and follow you'),
                  value: isPublic,
                  onChanged: (v) => setDialogState(() => isPublic = v),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
            FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Save')),
          ],
        ),
      ),
    );

    if (result == true && mounted) {
      try {
        final api = ref.read(apiServiceProvider);
        await api.updateSocialProfile(
          bio: bioController.text,
          isPublic: isPublic,
          readingGoal: int.tryParse(goalController.text),
        );
        _loadProfile();
      } catch (e) {
        if (!mounted) return;
        messenger.showSnackBar(
          SnackBar(content: Text(e.toString())),
        );
      }
    }
    bioController.dispose();
    goalController.dispose();
  }
}

class _StatColumn extends StatelessWidget {
  final int count;
  final String label;

  const _StatColumn({required this.count, required this.label});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      children: [
        Text(
          count.toString(),
          style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 4),
        Text(label, style: theme.textTheme.bodySmall),
      ],
    );
  }
}
