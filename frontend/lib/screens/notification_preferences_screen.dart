import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/notification_providers.dart';

/// Screen for managing notification category preferences (recommendations, social, marketing).
class NotificationPreferencesScreen extends ConsumerWidget {
  const NotificationPreferencesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final prefsAsync = ref.watch(notificationPreferencesProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Notification Settings')),
      body: prefsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.error_outline, size: 48, color: theme.colorScheme.error),
              const SizedBox(height: 16),
              Text('Failed to load preferences', style: theme.textTheme.titleMedium),
              const SizedBox(height: 8),
              FilledButton(
                onPressed: () => ref.invalidate(notificationPreferencesProvider),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
        data: (prefs) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(
              'Choose which notifications you want to receive',
              style: theme.textTheme.bodyLarge?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 24),
            Card(
              child: Column(
                children: [
                  SwitchListTile(
                    title: const Text('Recommendations'),
                    subtitle: const Text('New book picks based on your taste'),
                    secondary: const Icon(Icons.auto_awesome),
                    value: prefs.recommendations,
                    onChanged: (value) {
                      ref.read(notificationPreferencesProvider.notifier)
                          .updatePreference(recommendations: value);
                    },
                  ),
                  const Divider(height: 1),
                  SwitchListTile(
                    title: const Text('Social'),
                    subtitle: const Text('Friend activity and book club updates'),
                    secondary: const Icon(Icons.people),
                    value: prefs.social,
                    onChanged: (value) {
                      ref.read(notificationPreferencesProvider.notifier)
                          .updatePreference(social: value);
                    },
                  ),
                  const Divider(height: 1),
                  SwitchListTile(
                    title: const Text('Marketing'),
                    subtitle: const Text('Promotions and special offers'),
                    secondary: const Icon(Icons.campaign),
                    value: prefs.marketing,
                    onChanged: (value) {
                      ref.read(notificationPreferencesProvider.notifier)
                          .updatePreference(marketing: value);
                    },
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
