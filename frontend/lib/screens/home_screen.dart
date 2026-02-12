import 'package:cached_network_image/cached_network_image.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_card_swiper/flutter_card_swiper.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../models/book.dart';
import '../providers/providers.dart';
import '../theme/app_theme.dart';
import '../widgets/book_card.dart';
import '../widgets/swipe_overlay.dart';
import '../widgets/error_view.dart';
import '../widgets/loading_indicator.dart';

/// Main discovery screen — Tinder-style full-screen card swiping.
class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  final CardSwiperController _swiperController = CardSwiperController();

  // Track swipe progress for LIKE/NOPE overlay
  double _swipeProgress = 0.0;
  bool _swipingRight = false;

  @override
  void dispose() {
    _swiperController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final booksAsync = ref.watch(discoverBooksProvider);
    final user = ref.watch(authStateProvider).valueOrNull;

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // ── Tinder-style top bar ──
            _TopBar(
              onRefresh: () => ref.read(discoverBooksProvider.notifier).refresh(),
            ),

            // ── Swipe limit indicator (free users only) ──
            if (user != null && !user.isPremium) _buildSwipeIndicator(),

            // ── Card stack ──
            Expanded(
              child: booksAsync.when(
                loading: () => const LoadingIndicator(message: 'Finding books...'),
                error: (error, _) => ErrorView(
                  message: error.toString(),
                  onRetry: () => ref.read(discoverBooksProvider.notifier).refresh(),
                ),
                data: (books) {
                  if (books.isEmpty) return _buildEmptyState();
                  return _buildCardArea(books);
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Card area with swiper + action buttons ──
  Widget _buildCardArea(List<Book> books) {
    return Column(
      children: [
        // Card stack takes available space
        Expanded(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
            child: CardSwiper(
              controller: _swiperController,
              cardsCount: books.length,
              numberOfCardsDisplayed: books.length.clamp(1, 3),
              backCardOffset: const Offset(0, -40),
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              scale: 0.95,
              onSwipe: (previousIndex, currentIndex, direction) {
                _onSwipe(books[previousIndex], direction);
                final remaining = currentIndex == null ? 0 : books.length - currentIndex;
                ref.read(discoverBooksProvider.notifier).maybeLoadMore(remaining);
                setState(() => _swipeProgress = 0);
                return true;
              },
              onSwipeDirectionChange: (horizontalDirection, verticalDirection) {
                setState(() {
                  _swipingRight = horizontalDirection == CardSwiperDirection.right;
                  _swipeProgress = (horizontalDirection == CardSwiperDirection.right ||
                          horizontalDirection == CardSwiperDirection.left)
                      ? 0.8
                      : 0.0;
                });
              },
              onEnd: () {
                ref.read(discoverBooksProvider.notifier).loadMore();
              },
              cardBuilder: (context, index, percentThresholdX, percentThresholdY) {
                return Stack(
                  fit: StackFit.expand,
                  children: [
                    BookCard(
                      book: books[index],
                      onTap: () => _showBookDetail(books[index]),
                    ),
                    // LIKE / NOPE overlay
                    if (index == 0 && _swipeProgress > 0)
                      SwipeOverlay(
                        isLike: _swipingRight,
                        opacity: _swipeProgress,
                      ),
                  ],
                );
              },
            ),
          ),
        ),

        // ── Tinder action buttons ──
        _ActionButtons(
          onRewind: () => _handleRewind(),
          onNope: () => _swiperController.swipeLeft(),
          onSuperLike: () => _swiperController.swipe(CardSwiperDirection.top),
          onLike: () => _swiperController.swipeRight(),
        ),

        const SizedBox(height: 8),
      ],
    );
  }

  Widget _buildSwipeIndicator() {
    final swipeStatus = ref.watch(swipeStatusProvider);
    return swipeStatus.when(
      loading: () => const SizedBox.shrink(),
      error: (_, _) => const SizedBox.shrink(),
      data: (status) {
        final remaining = status['swipes_remaining'] as int? ?? 10;
        final limit = status['daily_limit'] as int? ?? 10;
        final used = status['swipes_today'] as int? ?? 0;

        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 4),
          child: Row(
            children: [
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(3),
                  child: LinearProgressIndicator(
                    value: (used / limit).clamp(0.0, 1.0),
                    backgroundColor: Colors.grey.shade200,
                    valueColor: AlwaysStoppedAnimation(
                      used >= limit ? AppTheme.nopeRed : AppTheme.tinderRed,
                    ),
                    minHeight: 4,
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Text(
                '$remaining left',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: remaining <= 3 ? AppTheme.nopeRed : AppTheme.textSecondary,
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  void _onSwipe(Book book, CardSwiperDirection direction) {
    HapticFeedback.mediumImpact();
    if (direction == CardSwiperDirection.right) {
      _handleLikeSwipe(book);
    } else if (direction == CardSwiperDirection.left) {
      _handleSkipSwipe(book);
    } else if (direction == CardSwiperDirection.top) {
      // Super like = also a like
      _handleLikeSwipe(book);
    }
  }

  Future<void> _handleLikeSwipe(Book book) async {
    try {
      await ref.read(likedBooksProvider.notifier).likeBook(book);
      ref.read(discoverBooksProvider.notifier).setLastSwiped(book, wasLiked: true);
      ref.invalidate(swipeStatusProvider);
    } on DioException catch (e) {
      if (e.response?.statusCode == 429) {
        _showUpgradePrompt();
      }
    }
  }

  Future<void> _handleSkipSwipe(Book book) async {
    try {
      final api = ref.read(apiServiceProvider);
      await api.skipBook(book.id);
      ref.read(discoverBooksProvider.notifier).setLastSwiped(book, wasLiked: false);
      ref.invalidate(swipeStatusProvider);
    } on DioException catch (e) {
      if (e.response?.statusCode == 429) {
        _showUpgradePrompt();
      }
    }
  }

  void _handleRewind() {
    HapticFeedback.lightImpact();
    ref.read(discoverBooksProvider.notifier).undoLastSwipe();
  }

  void _showBookDetail(Book book) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _BookDetailSheet(book: book),
    );
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

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.auto_stories_rounded,
            size: 80,
            color: Theme.of(context).colorScheme.onSurfaceVariant.withValues(alpha: 0.4),
          ),
          const SizedBox(height: 16),
          Text(
            'No more books!',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
          ),
          const SizedBox(height: 8),
          Text(
            'Try a different category or check back later.',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppTheme.textSecondary,
                ),
          ),
          const SizedBox(height: 28),
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

// ═══════════════════════════════════════════════════════════════
//  Tinder-style top bar: logo centre, no heavy AppBar
// ═══════════════════════════════════════════════════════════════

class _TopBar extends StatelessWidget {
  final VoidCallback onRefresh;
  const _TopBar({required this.onRefresh});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          // Settings / profile icon
          _TopBarIcon(
            icon: Icons.tune_rounded,
            onTap: () => context.go('/categories'),
          ),
          const Spacer(),
          // Centre logo
          ShaderMask(
            shaderCallback: (bounds) => AppTheme.tinderGradient.createShader(bounds),
            child: const Icon(
              Icons.local_fire_department,
              size: 36,
              color: Colors.white,
            ),
          ),
          const Spacer(),
          // Refresh
          _TopBarIcon(icon: Icons.refresh_rounded, onTap: onRefresh),
        ],
      ),
    );
  }
}

class _TopBarIcon extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  const _TopBarIcon({required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Icon(icon, size: 28, color: AppTheme.textSecondary),
    );
  }
}

// ═══════════════════════════════════════════════════════════════
//  Tinder-style circular action buttons
// ═══════════════════════════════════════════════════════════════

class _ActionButtons extends StatelessWidget {
  final VoidCallback onRewind;
  final VoidCallback onNope;
  final VoidCallback onSuperLike;
  final VoidCallback onLike;

  const _ActionButtons({
    required this.onRewind,
    required this.onNope,
    required this.onSuperLike,
    required this.onLike,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          // Rewind (small)
          _CircleButton(
            icon: Icons.replay_rounded,
            color: AppTheme.rewindYellow,
            size: 44,
            iconSize: 22,
            onTap: onRewind,
          ),
          // Nope / X (large)
          _CircleButton(
            icon: Icons.close_rounded,
            color: AppTheme.nopeRed,
            size: 60,
            iconSize: 32,
            onTap: onNope,
          ),
          // Super Like / Star (small)
          _CircleButton(
            icon: Icons.star_rounded,
            color: AppTheme.superLikeBlue,
            size: 44,
            iconSize: 22,
            onTap: onSuperLike,
          ),
          // Like / Heart (large)
          _CircleButton(
            icon: Icons.favorite_rounded,
            color: AppTheme.likeGreen,
            size: 60,
            iconSize: 32,
            onTap: onLike,
          ),
        ],
      ),
    );
  }
}

class _CircleButton extends StatelessWidget {
  final IconData icon;
  final Color color;
  final double size;
  final double iconSize;
  final VoidCallback onTap;

  const _CircleButton({
    required this.icon,
    required this.color,
    required this.size,
    required this.iconSize,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: Theme.of(context).scaffoldBackgroundColor,
          border: Border.all(color: color.withValues(alpha: 0.3), width: 2),
          boxShadow: [
            BoxShadow(
              color: color.withValues(alpha: 0.15),
              blurRadius: 12,
              spreadRadius: 1,
            ),
          ],
        ),
        child: Icon(icon, color: color, size: iconSize),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════
//  Book detail bottom sheet (tap on card to expand)
// ═══════════════════════════════════════════════════════════════

class _BookDetailSheet extends StatelessWidget {
  final Book book;
  const _BookDetailSheet({required this.book});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return DraggableScrollableSheet(
      initialChildSize: 0.85,
      minChildSize: 0.5,
      maxChildSize: 0.95,
      builder: (context, controller) {
        return Container(
          decoration: BoxDecoration(
            color: theme.scaffoldBackgroundColor,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: ListView(
            controller: controller,
            padding: EdgeInsets.zero,
            children: [
              // Drag handle
              Center(
                child: Container(
                  margin: const EdgeInsets.only(top: 12, bottom: 8),
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: Colors.grey.shade400,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),

              // Cover image
              if (book.highResThumbnail.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: AspectRatio(
                      aspectRatio: 2 / 3,
                      child: Hero(
                        tag: 'book-cover-${book.id}',
                        child: CachedNetworkImage(
                          imageUrl: book.highResThumbnail,
                          fit: BoxFit.cover,
                          memCacheWidth: 800,
                          maxWidthDiskCache: 800,
                          errorWidget: (_, __, ___) => Container(
                            color: theme.colorScheme.surfaceContainerHighest,
                            child: const Center(child: Icon(Icons.book, size: 80)),
                          ),
                        ),
                      ),
                    ),
                  ),
                ),

              Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Title
                    Text(
                      book.title,
                      style: theme.textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 4),
                    // Author
                    Text(
                      book.authorsText,
                      style: theme.textTheme.titleMedium?.copyWith(
                        color: AppTheme.tinderRed,
                        fontWeight: FontWeight.w500,
                      ),
                    ),

                    const SizedBox(height: 16),

                    // Stats row
                    Row(
                      children: [
                        if (book.averageRating != null) ...[
                          const Icon(Icons.star_rounded, size: 20, color: AppTheme.rewindYellow),
                          const SizedBox(width: 4),
                          Text(
                            '${book.averageRating!.toStringAsFixed(1)}',
                            style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                          ),
                          if (book.ratingsCount != null)
                            Text(
                              ' (${book.ratingsCount} ratings)',
                              style: theme.textTheme.bodySmall?.copyWith(color: AppTheme.textSecondary),
                            ),
                          const SizedBox(width: 16),
                        ],
                        if (book.pageCount != null) ...[
                          Icon(Icons.menu_book_rounded, size: 18, color: AppTheme.textSecondary),
                          const SizedBox(width: 4),
                          Text(
                            '${book.pageCount} pages',
                            style: theme.textTheme.bodySmall?.copyWith(color: AppTheme.textSecondary),
                          ),
                        ],
                      ],
                    ),

                    // Categories
                    if (book.categories.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      Wrap(
                        spacing: 8,
                        runSpacing: 6,
                        children: book.categories.map((cat) {
                          return Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                            decoration: BoxDecoration(
                              color: AppTheme.tinderRed.withValues(alpha: 0.1),
                              borderRadius: BorderRadius.circular(16),
                            ),
                            child: Text(
                              cat,
                              style: TextStyle(
                                color: AppTheme.tinderRed,
                                fontSize: 13,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          );
                        }).toList(),
                      ),
                    ],

                    // Description
                    if (book.description != null && book.description!.isNotEmpty) ...[
                      const SizedBox(height: 20),
                      Text(
                        'About this book',
                        style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        book.description!,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          height: 1.5,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                    ],

                    // Publisher / Date
                    if (book.publisher != null || book.publishedDate != null) ...[
                      const SizedBox(height: 20),
                      if (book.publisher != null)
                        Text(
                          'Published by ${book.publisher}',
                          style: theme.textTheme.bodySmall?.copyWith(color: AppTheme.textSecondary),
                        ),
                      if (book.publishedDate != null)
                        Text(
                          book.publishedDate!,
                          style: theme.textTheme.bodySmall?.copyWith(color: AppTheme.textSecondary),
                        ),
                    ],

                    const SizedBox(height: 32),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
