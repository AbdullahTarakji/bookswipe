import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../models/category.dart';
import '../providers/onboarding_provider.dart';
import '../providers/providers.dart';
import '../widgets/responsive_container.dart';

/// Screen for selecting favourite genres during onboarding.
/// Requires at least 3 selections before proceeding.
class GenreSelectionScreen extends ConsumerStatefulWidget {
  const GenreSelectionScreen({super.key});

  @override
  ConsumerState<GenreSelectionScreen> createState() =>
      _GenreSelectionScreenState();
}

class _GenreSelectionScreenState extends ConsumerState<GenreSelectionScreen> {
  final Set<String> _selected = {};

  static const int _minSelections = 3;

  bool get _canProceed => _selected.length >= _minSelections;

  Future<void> _finish() async {
    if (!_canProceed) return;

    // Save selected genres to backend preferences
    try {
      final api = ref.read(apiServiceProvider);
      await api.updateGenrePreferences(_selected.toList());
    } catch (_) {
      // Non-blocking — preferences will be built from swipe history anyway
    }

    // Mark onboarding complete
    await ref.read(onboardingCompleteProvider.notifier).complete();

    if (mounted) {
      context.go('/');
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    const categories = BookCategory.defaults;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Pick Your Genres'),
        automaticallyImplyLeading: false,
        actions: [
          TextButton(
            onPressed: () async {
              await ref.read(onboardingCompleteProvider.notifier).complete();
              if (context.mounted) context.go('/');
            },
            child: const Text('Skip'),
          ),
        ],
      ),
      body: ResponsiveContainer(
        maxWidth: 500,
        child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
            child: Text(
              'Choose at least $_minSelections genres you love',
              style: theme.textTheme.bodyLarge?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ),
          Expanded(
            child: GridView.builder(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 3,
                childAspectRatio: 0.9,
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
              ),
              itemCount: categories.length,
              itemBuilder: (context, index) {
                final cat = categories[index];
                final isSelected = _selected.contains(cat.key);
                return GestureDetector(
                  onTap: () {
                    setState(() {
                      if (isSelected) {
                        _selected.remove(cat.key);
                      } else {
                        _selected.add(cat.key);
                      }
                    });
                  },
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    decoration: BoxDecoration(
                      color: isSelected
                          ? cat.color.withValues(alpha: 0.15)
                          : theme.colorScheme.surfaceContainerHighest,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(
                        color: isSelected ? cat.color : Colors.transparent,
                        width: 2,
                      ),
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          cat.icon,
                          size: 36,
                          color: isSelected
                              ? cat.color
                              : theme.colorScheme.onSurfaceVariant,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          cat.name,
                          style: theme.textTheme.bodySmall?.copyWith(
                            fontWeight: isSelected
                                ? FontWeight.bold
                                : FontWeight.normal,
                            color: isSelected
                                ? cat.color
                                : theme.colorScheme.onSurfaceVariant,
                          ),
                          textAlign: TextAlign.center,
                        ),
                        if (isSelected)
                          Padding(
                            padding: const EdgeInsets.only(top: 4),
                            child: Icon(
                              Icons.check_circle,
                              size: 18,
                              color: cat.color,
                            ),
                          ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          // Bottom bar
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: _canProceed ? _finish : null,
                  child: Text(
                    _canProceed
                        ? 'Continue (${_selected.length} selected)'
                        : 'Select at least $_minSelections genres',
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
      ),
    );
  }
}
