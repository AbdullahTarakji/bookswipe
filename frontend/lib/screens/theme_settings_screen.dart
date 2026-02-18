import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/theme_provider.dart';

/// Screen for selecting light, dark, or system theme mode.
class ThemeSettingsScreen extends ConsumerWidget {
  const ThemeSettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentMode = ref.watch(themeModeProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Appearance')),
      body: ListView(
        padding: const EdgeInsets.symmetric(vertical: 8),
        children: [
          _ThemeOption(
            icon: Icons.brightness_auto,
            title: 'System',
            subtitle: 'Follow device setting',
            selected: currentMode == ThemeMode.system,
            onTap: () => ref
                .read(themeModeProvider.notifier)
                .setThemeMode(ThemeMode.system),
          ),
          _ThemeOption(
            icon: Icons.light_mode,
            title: 'Light',
            subtitle: 'Always use light theme',
            selected: currentMode == ThemeMode.light,
            onTap: () => ref
                .read(themeModeProvider.notifier)
                .setThemeMode(ThemeMode.light),
          ),
          _ThemeOption(
            icon: Icons.dark_mode,
            title: 'Dark',
            subtitle: 'Always use dark theme',
            selected: currentMode == ThemeMode.dark,
            onTap: () => ref
                .read(themeModeProvider.notifier)
                .setThemeMode(ThemeMode.dark),
          ),
        ],
      ),
    );
  }
}

class _ThemeOption extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final bool selected;
  final VoidCallback onTap;

  const _ThemeOption({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return ListTile(
      leading: Icon(icon, color: selected ? theme.colorScheme.primary : null),
      title: Text(title),
      subtitle: Text(subtitle),
      trailing: selected
          ? Icon(Icons.check_circle, color: theme.colorScheme.primary)
          : null,
      onTap: onTap,
    );
  }
}
