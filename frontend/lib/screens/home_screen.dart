import 'package:flutter/material.dart';
import 'package:flutter_card_swiper/flutter_card_swiper.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../models/book.dart';
import '../models/category.dart';
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

  Widget _buildCategoryChips(String? selectedCategory) {
    return SizedBox(
      height: 50,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        itemCount: BookCategory.defaults.length + 1,
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
          final cat = BookCategory.defaults[index - 1];
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
      ref.read(likedBooksProvider.notifier).likeBook(book);
      _showSwipeFeedback(true);
    } else if (direction == CardSwiperDirection.left) {
      final api = ref.read(apiServiceProvider);
      api.skipBook(book.id);
      _showSwipeFeedback(false);
    }
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
