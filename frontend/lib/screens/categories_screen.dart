import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/providers.dart';
import '../theme/app_theme.dart';
import '../widgets/loading_indicator.dart';

class CategoriesScreen extends ConsumerWidget {
  const CategoriesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedCategory = ref.watch(selectedCategoryProvider);
    final categoriesAsync = ref.watch(categoriesProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            ShaderMask(
              shaderCallback: (bounds) => AppTheme.brandGradient.createShader(bounds),
              child: const Icon(Icons.grid_view, size: 22, color: Colors.white),
            ),
            const SizedBox(width: 8),
            const Text('Explore'),
          ],
        ),
      ),
      body: categoriesAsync.when(
        loading: () => const LoadingIndicator(message: 'Loading categories...'),
        error: (error, _) => Center(child: Text('Failed to load: $error')),
        data: (categories) => GridView.builder(
          padding: const EdgeInsets.all(16),
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            childAspectRatio: 1.4,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
          ),
          itemCount: categories.length,
          itemBuilder: (context, index) {
            final cat = categories[index];
            final isSelected = selectedCategory == cat.key;

            return GestureDetector(
              onTap: () {
                ref.read(selectedCategoryProvider.notifier).state =
                    isSelected ? null : cat.key;
              },
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                decoration: BoxDecoration(
                  gradient: isSelected
                      ? LinearGradient(
                          colors: [
                            cat.color.withValues(alpha: 0.25),
                            cat.color.withValues(alpha: 0.08),
                          ],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        )
                      : null,
                  color: isSelected ? null : (theme.cardTheme.color ?? theme.colorScheme.surface),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: isSelected ? cat.color : Colors.transparent,
                    width: 2,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: (isSelected ? cat.color : Colors.black).withValues(alpha: 0.1),
                      blurRadius: 10,
                      offset: const Offset(0, 3),
                    ),
                  ],
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      cat.icon,
                      size: 36,
                      color: isSelected ? cat.color : theme.colorScheme.onSurfaceVariant,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      cat.name,
                      style: theme.textTheme.titleSmall?.copyWith(
                        fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                        color: isSelected ? cat.color : theme.colorScheme.onSurface,
                      ),
                    ),
                    if (isSelected)
                      Padding(
                        padding: const EdgeInsets.only(top: 4),
                        child: Icon(Icons.check_circle, size: 16, color: cat.color),
                      ),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
