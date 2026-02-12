import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_card_swiper/flutter_card_swiper.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../models/book.dart';
import '../providers/providers.dart';
import '../widgets/book_card.dart';
import '../widgets/error_view.dart';
import '../widgets/loading_indicator.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  final CardSwiperController _swiperController = CardSwiperController();

  @override
  void dispose() {
    _swiperController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final booksAsync = ref.watch(discoverBooksProvider);
    final selectedCategory = ref.watch(selectedCategoryProvider);
    final user = ref.watch(authStateProvider).valueOrNull;

    return Scaffold(
      appBar: AppBar(
        title: const Text('BookSwipe'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(discoverBooksProvider.notifier).refresh(),
          ),
        ],
      ),
      body: Column(
        children: [
          _buildCategoryChips(selectedCategory),
          if (user != null && !user.isPremium) _buildSwipeIndicator(),
          Expanded(
            child: booksAsync.when(
              loading: () => const LoadingIndicator(message: 'Finding books...'),
              error: (error, _) => ErrorView(
                message: error.toString(),
                onRetry: () => ref.read(discoverBooksProvider.notifier).refresh(),
              ),
              data: (books) {
                if (books.isEmpty) {
                  return _buildEmptyState();
                }
                return _buildSwiper(books);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSwipeIndicator() {
    final swipeStatus = ref.watch(swipeStatusProvider);
    return swipeStatus.when(
      loading: () => const SizedBox.shrink(),
      error: (_, _) => const SizedBox.shrink(),
      data: (status) {
        final swipesRemaining = status['swipes_remaining'] as int? ?? 10;
        final dailyLimit = status['daily_limit'] as int? ?? 10;
        final swipesToday = status['swipes_today'] as int? ?? 0;

        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
          child: Row(
            children: [
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: swipesToday / dailyLimit,
                    backgroundColor: Theme.of(context).colorScheme.surfaceContainerHighest,
                    minHeight: 6,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Text(
                '$swipesRemaining/$dailyLimit',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildCategoryChips(String? selectedCategory) {
    final categoriesAsync = ref.watch(categoriesProvider);
    final categories = categoriesAsync.valueOrNull ?? [];

    return SizedBox(
      height: 50,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        itemCount: categories.length + 1,
        itemBuilder: (context, index) {
          if (index == 0) {
            return Padding(
              padding: const EdgeInsets.only(right: 8),
              child: FilterChip(
                label: const Text('All'),
                selected: selectedCategory == null,
                onSelected: (_) {
                  ref.read(selectedCategoryProvider.notifier).state = null;
                },
              ),
            );
          }
          final cat = categories[index - 1];
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: FilterChip(
              avatar: Icon(cat.icon, size: 18),
              label: Text(cat.name),
              selected: selectedCategory == cat.key,
              onSelected: (_) {
                ref.read(selectedCategoryProvider.notifier).state =
                    selectedCategory == cat.key ? null : cat.key;
              },
            ),
          );
        },
      ),
    );
  }

  Widget _buildSwiper(List<Book> books) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: CardSwiper(
        controller: _swiperController,
        cardsCount: books.length,
        numberOfCardsDisplayed: books.length.clamp(1, 3),
        backCardOffset: const Offset(0, -30),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
        onSwipe: (previousIndex, currentIndex, direction) {
          _onSwipe(books[previousIndex], direction);
          if (currentIndex != null && currentIndex >= books.length - 2) {
            ref.read(discoverBooksProvider.notifier).loadMore();
          }
          return true;
        },
        onEnd: () {
          ref.read(discoverBooksProvider.notifier).loadMore();
        },
        cardBuilder: (context, index, percentThresholdX, percentThresholdY) {
          return BookCard(
            book: books[index],
            onTap: () => context.push('/book/${books[index].id}'),
          );
        },
      ),
    );
  }

  void _onSwipe(Book book, CardSwiperDirection direction) {
    if (direction == CardSwiperDirection.right) {
      _handleLikeSwipe(book);
    } else if (direction == CardSwiperDirection.left) {
      _handleSkipSwipe(book);
    }
  }

  Future<void> _handleLikeSwipe(Book book) async {
    try {
      await ref.read(likedBooksProvider.notifier).likeBook(book);
      _showSwipeFeedback(true);
      ref.invalidate(swipeStatusProvider);
    } on DioException catch (e) {
      if (e.response?.statusCode == 429) {
        _showUpgradePrompt();
        return;
      }
      _showSwipeFeedback(true);
    }
  }

  Future<void> _handleSkipSwipe(Book book) async {
    try {
      final api = ref.read(apiServiceProvider);
      await api.skipBook(book.id);
      _showSwipeFeedback(false);
      ref.invalidate(swipeStatusProvider);
    } on DioException catch (e) {
      if (e.response?.statusCode == 429) {
        _showUpgradePrompt();
        return;
      }
      _showSwipeFeedback(false);
    }
  }

  void _showUpgradePrompt() {
    if (!mounted) return;
    ScaffoldMessenger.of(context).clearSnackBars();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text('Daily swipe limit reached!'),
        action: SnackBarAction(
          label: 'Upgrade',
          onPressed: () => context.push('/subscription'),
        ),
        duration: const Duration(seconds: 4),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  void _showSwipeFeedback(bool isLike) {
    ScaffoldMessenger.of(context).clearSnackBars();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(isLike ? 'Added to liked books!' : 'Skipped'),
        duration: const Duration(milliseconds: 800),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.auto_stories,
            size: 80,
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
          const SizedBox(height: 16),
          Text(
            'No more books to discover!',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 8),
          Text(
            'Try a different category or refresh.',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: 24),
          FilledButton.icon(
            onPressed: () => ref.read(discoverBooksProvider.notifier).refresh(),
            icon: const Icon(Icons.refresh),
            label: const Text('Refresh'),
          ),
        ],
      ),
    );
  }
}
