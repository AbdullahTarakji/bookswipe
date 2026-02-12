import 'package:flutter/material.dart';
import 'package:shimmer/shimmer.dart';

/// A shimmer placeholder box used to build loading skeletons.
///
/// Renders a rounded rectangle with a shimmer animation effect,
/// providing a visual hint that content is loading.
class ShimmerBox extends StatelessWidget {
  /// Width of the shimmer box. Defaults to full available width.
  final double? width;

  /// Height of the shimmer box.
  final double height;

  /// Border radius of the shimmer box.
  final double borderRadius;

  /// Creates a shimmer placeholder box.
  const ShimmerBox({
    super.key,
    this.width,
    required this.height,
    this.borderRadius = 8,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(borderRadius),
      ),
    );
  }
}

/// Shimmer loading skeleton for the home screen card stack.
///
/// Mimics the appearance of a [BookCard] with placeholder elements
/// for the cover image, title, author, and rating.
class HomeShimmer extends StatelessWidget {
  /// Creates a home screen shimmer skeleton.
  const HomeShimmer({super.key});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      child: Shimmer.fromColors(
        baseColor: isDark ? Colors.grey.shade800 : Colors.grey.shade300,
        highlightColor:
            isDark ? Colors.grey.shade700 : Colors.grey.shade100,
        child: Card(
          child: Stack(
            fit: StackFit.expand,
            children: [
              // Cover placeholder
              Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              // Bottom info placeholder
              const Positioned(
                left: 20,
                right: 20,
                bottom: 24,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    ShimmerBox(width: 200, height: 24),
                    SizedBox(height: 8),
                    ShimmerBox(width: 140, height: 16),
                    SizedBox(height: 10),
                    Row(
                      children: [
                        ShimmerBox(width: 50, height: 14),
                        SizedBox(width: 12),
                        ShimmerBox(width: 70, height: 22, borderRadius: 12),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Shimmer loading skeleton for the favorites/liked books list.
///
/// Mimics the appearance of [BookListTile] items with placeholder
/// elements for the thumbnail, title, author, and rating badge.
class FavoritesShimmer extends StatelessWidget {
  /// Number of placeholder list items to display.
  final int itemCount;

  /// Creates a favorites screen shimmer skeleton.
  const FavoritesShimmer({super.key, this.itemCount = 6});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Shimmer.fromColors(
      baseColor: isDark ? Colors.grey.shade800 : Colors.grey.shade300,
      highlightColor: isDark ? Colors.grey.shade700 : Colors.grey.shade100,
      child: ListView.separated(
        padding: const EdgeInsets.symmetric(vertical: 8),
        itemCount: itemCount,
        physics: const NeverScrollableScrollPhysics(),
        separatorBuilder: (_, _) => const SizedBox(height: 2),
        itemBuilder: (_, _) => const _FavoriteItemShimmer(),
      ),
    );
  }
}

class _FavoriteItemShimmer extends StatelessWidget {
  const _FavoriteItemShimmer();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        children: [
          // Thumbnail placeholder
          ShimmerBox(width: 56, height: 80, borderRadius: 10),
          SizedBox(width: 14),
          // Title and author placeholders
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                ShimmerBox(height: 16),
                SizedBox(height: 6),
                ShimmerBox(width: 120, height: 12),
              ],
            ),
          ),
          SizedBox(width: 8),
          // Rating badge placeholder
          ShimmerBox(width: 48, height: 28, borderRadius: 8),
        ],
      ),
    );
  }
}

/// Shimmer loading skeleton for the book detail screen.
///
/// Mimics the full book detail layout with placeholders for the
/// cover image, title, author, metadata, and description.
class BookDetailShimmer extends StatelessWidget {
  /// Creates a book detail screen shimmer skeleton.
  const BookDetailShimmer({super.key});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Shimmer.fromColors(
      baseColor: isDark ? Colors.grey.shade800 : Colors.grey.shade300,
      highlightColor: isDark ? Colors.grey.shade700 : Colors.grey.shade100,
      child: CustomScrollView(
        physics: const NeverScrollableScrollPhysics(),
        slivers: [
          // Cover image placeholder
          SliverAppBar(
            expandedHeight: 350,
            pinned: true,
            flexibleSpace: FlexibleSpaceBar(
              background: Container(color: Colors.white),
            ),
          ),
          const SliverToBoxAdapter(
            child: Padding(
              padding: EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Title
                  ShimmerBox(width: 250, height: 24),
                  SizedBox(height: 12),
                  // Author
                  ShimmerBox(width: 160, height: 18),
                  SizedBox(height: 20),
                  // Metadata row
                  Row(
                    children: [
                      ShimmerBox(width: 60, height: 16),
                      SizedBox(width: 16),
                      ShimmerBox(width: 80, height: 16),
                    ],
                  ),
                  SizedBox(height: 24),
                  // Like button
                  ShimmerBox(height: 48, borderRadius: 24),
                  SizedBox(height: 24),
                  // Category chips
                  Row(
                    children: [
                      ShimmerBox(width: 70, height: 32, borderRadius: 16),
                      SizedBox(width: 8),
                      ShimmerBox(width: 90, height: 32, borderRadius: 16),
                    ],
                  ),
                  SizedBox(height: 24),
                  // Description header
                  ShimmerBox(width: 100, height: 18),
                  SizedBox(height: 12),
                  // Description lines
                  ShimmerBox(height: 14),
                  SizedBox(height: 8),
                  ShimmerBox(height: 14),
                  SizedBox(height: 8),
                  ShimmerBox(width: 200, height: 14),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
