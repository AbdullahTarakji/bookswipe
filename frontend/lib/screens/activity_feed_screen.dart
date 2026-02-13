import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/social_providers.dart';
import '../widgets/empty_state.dart';
import '../widgets/error_view.dart';
import '../widgets/shimmer_loading.dart';

/// Displays the user's social activity feed.
class ActivityFeedScreen extends ConsumerWidget {
  const ActivityFeedScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final feedState = ref.watch(activityFeedProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Activity Feed')),
      body: feedState.when(
        loading: () => const FavoritesShimmer(),
        error: (error, _) => ErrorView(
          message: error.toString(),
          onRetry: () => ref.invalidate(activityFeedProvider),
        ),
        data: (data) {
          final events = (data['events'] as List<dynamic>?) ?? [];
          if (events.isEmpty) {
            return const EmptyState(
              icon: Icons.rss_feed,
              title: 'No activity yet',
              subtitle: 'Follow people to see their activity here',
            );
          }
          return RefreshIndicator(
            onRefresh: () => ref.read(activityFeedProvider.notifier).refresh(),
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(vertical: 8),
              itemCount: events.length,
              itemBuilder: (context, index) {
                final event = events[index] as Map<String, dynamic>;
                return _ActivityTile(event: event, theme: theme);
              },
            ),
          );
        },
      ),
    );
  }
}

class _ActivityTile extends StatelessWidget {
  final Map<String, dynamic> event;
  final ThemeData theme;

  const _ActivityTile({required this.event, required this.theme});

  @override
  Widget build(BuildContext context) {
    final eventType = event['event_type'] as String? ?? '';
    final username = event['username'] as String? ?? 'Unknown';
    final metadata = event['metadata'] as Map<String, dynamic>? ?? {};
    final createdAt = event['created_at'] as String? ?? '';

    IconData icon;
    String description;

    switch (eventType) {
      case 'liked_book':
        icon = Icons.favorite;
        final bookTitle = metadata['book_title'] as String? ?? 'a book';
        description = '$username liked "$bookTitle"';
      case 'created_list':
        icon = Icons.playlist_add;
        final listName = metadata['list_name'] as String? ?? 'a list';
        description = '$username created list "$listName"';
      case 'followed_user':
        icon = Icons.person_add;
        final followedUser = metadata['followed_username'] as String? ?? 'someone';
        description = '$username followed $followedUser';
      default:
        icon = Icons.circle;
        description = '$username performed an action';
    }

    return ListTile(
      leading: CircleAvatar(
        backgroundColor: theme.colorScheme.primaryContainer,
        child: Icon(icon, color: theme.colorScheme.onPrimaryContainer, size: 20),
      ),
      title: Text(description),
      subtitle: Text(_formatTime(createdAt), style: theme.textTheme.bodySmall),
      onTap: () {
        final userId = event['user_id'] as int?;
        if (userId != null) {
          context.push('/social/profile/$userId');
        }
      },
    );
  }

  String _formatTime(String isoString) {
    if (isoString.isEmpty) return '';
    try {
      final dt = DateTime.parse(isoString);
      final diff = DateTime.now().difference(dt);
      if (diff.inMinutes < 1) return 'Just now';
      if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
      if (diff.inHours < 24) return '${diff.inHours}h ago';
      if (diff.inDays < 7) return '${diff.inDays}d ago';
      return '${dt.month}/${dt.day}/${dt.year}';
    } catch (_) {
      return '';
    }
  }
}
