import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/providers.dart';

class AdminSystemScreen extends ConsumerWidget {
  const AdminSystemScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final systemAsync = ref.watch(adminSystemInfoProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('System Info'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.invalidate(adminSystemInfoProvider),
          ),
        ],
      ),
      body: systemAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('Error: $error'),
              const SizedBox(height: 16),
              FilledButton(
                onPressed: () => ref.invalidate(adminSystemInfoProvider),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
        data: (info) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _InfoSection(
              title: 'Application',
              items: {
                'Version': info['app_version']?.toString() ?? '-',
                'Environment': info['environment']?.toString() ?? '-',
                'PID': info['pid']?.toString() ?? '-',
              },
            ),
            const SizedBox(height: 16),
            _InfoSection(
              title: 'Runtime',
              items: {
                'Python Version': info['python_version']?.toString() ?? '-',
                'Platform': info['platform']?.toString() ?? '-',
                'Uptime': info['uptime_human']?.toString() ?? '-',
                'Memory Usage': '${info['memory_usage_mb'] ?? 0} MB',
              },
            ),
            const SizedBox(height: 16),
            _InfoSection(
              title: 'Database',
              items: _mapToStringMap(info['database'] as Map<String, dynamic>? ?? {}),
            ),
            const SizedBox(height: 16),
            _InfoSection(
              title: 'Redis',
              items: _mapToStringMap(info['redis'] as Map<String, dynamic>? ?? {}),
            ),
          ],
        ),
      ),
    );
  }

  Map<String, String> _mapToStringMap(Map<String, dynamic> map) {
    return map.map((k, v) => MapEntry(
          k.replaceAll('_', ' ').replaceFirst(k[0], k[0].toUpperCase()),
          v?.toString() ?? '-',
        ));
  }
}

class _InfoSection extends StatelessWidget {
  final String title;
  final Map<String, String> items;

  const _InfoSection({required this.title, required this.items});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
            const Divider(),
            ...items.entries.map(
              (e) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(e.key, style: theme.textTheme.bodyMedium),
                    Flexible(
                      child: Text(
                        e.value,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: theme.colorScheme.onSurfaceVariant,
                        ),
                        textAlign: TextAlign.end,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
