import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/providers.dart';
import '../providers/review_providers.dart';
import 'star_rating.dart';

/// Reviews section displayed on the book detail screen.
class ReviewSection extends ConsumerStatefulWidget {
  final String bookId;

  const ReviewSection({super.key, required this.bookId});

  @override
  ConsumerState<ReviewSection> createState() => _ReviewSectionState();
}

class _ReviewSectionState extends ConsumerState<ReviewSection> {
  String _sort = 'newest';

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final param = ReviewsParam(widget.bookId, sort: _sort);
    final reviewsAsync = ref.watch(bookReviewsProvider(param));

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 24),
        const Divider(),
        const SizedBox(height: 8),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('Reviews', style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
            TextButton.icon(
              onPressed: () => _showWriteReviewDialog(context),
              icon: const Icon(Icons.rate_review, size: 18),
              label: const Text('Write Review'),
            ),
          ],
        ),
        const SizedBox(height: 8),
        reviewsAsync.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => Text('Failed to load reviews', style: TextStyle(color: theme.colorScheme.error)),
          data: (data) => _buildReviewsContent(context, data),
        ),
      ],
    );
  }

  Widget _buildReviewsContent(BuildContext context, Map<String, dynamic> data) {
    final theme = Theme.of(context);
    final reviews = data['reviews'] as List? ?? [];
    final avgRating = data['average_rating'];
    final totalRatings = data['total_ratings'] ?? 0;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (avgRating != null) ...[
          Row(
            children: [
              StarRating(rating: (avgRating as num).toDouble(), size: 28),
              const SizedBox(width: 8),
              Text(
                '${avgRating.toStringAsFixed(1)} ($totalRatings ${totalRatings == 1 ? 'rating' : 'ratings'})',
                style: theme.textTheme.titleMedium,
              ),
            ],
          ),
          const SizedBox(height: 12),
        ],
        // Sort toggle
        Row(
          children: [
            ChoiceChip(
              label: const Text('Newest'),
              selected: _sort == 'newest',
              onSelected: (_) => setState(() => _sort = 'newest'),
            ),
            const SizedBox(width: 8),
            ChoiceChip(
              label: const Text('Most Helpful'),
              selected: _sort == 'helpful',
              onSelected: (_) => setState(() => _sort = 'helpful'),
            ),
          ],
        ),
        const SizedBox(height: 12),
        if (reviews.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 16),
            child: Text('No reviews yet. Be the first to review!'),
          )
        else
          ...reviews.map((r) => _ReviewCard(
                review: r as Map<String, dynamic>,
                bookId: widget.bookId,
                sort: _sort,
              )),
      ],
    );
  }

  void _showWriteReviewDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (_) => _WriteReviewDialog(bookId: widget.bookId, sort: _sort),
    );
  }
}

class _ReviewCard extends ConsumerWidget {
  final Map<String, dynamic> review;
  final String bookId;
  final String sort;

  const _ReviewCard({required this.review, required this.bookId, required this.sort});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final rating = review['rating'] as int;
    final text = review['review_text'] as String? ?? '';
    final username = review['username'] as String? ?? 'Anonymous';
    final helpfulCount = review['helpful_count'] as int? ?? 0;
    final hasVoted = review['user_has_voted'] as bool? ?? false;
    final reviewId = review['id'] as int;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Text(username, style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                    const SizedBox(width: 8),
                    StarRating(rating: rating.toDouble(), size: 16),
                  ],
                ),
              ],
            ),
            if (text.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(text, style: theme.textTheme.bodyMedium),
            ],
            const SizedBox(height: 8),
            Row(
              children: [
                TextButton.icon(
                  onPressed: () => _toggleHelpful(ref, reviewId, hasVoted),
                  icon: Icon(
                    hasVoted ? Icons.thumb_up : Icons.thumb_up_outlined,
                    size: 16,
                  ),
                  label: Text('Helpful ($helpfulCount)'),
                  style: TextButton.styleFrom(
                    foregroundColor: hasVoted ? theme.colorScheme.primary : null,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _toggleHelpful(WidgetRef ref, int reviewId, bool hasVoted) async {
    final api = ref.read(apiServiceProvider);
    try {
      if (hasVoted) {
        await api.removeReviewVote(reviewId);
      } else {
        await api.voteReviewHelpful(reviewId);
      }
      ref.invalidate(bookReviewsProvider(ReviewsParam(bookId, sort: sort)));
    } catch (_) {}
  }
}

class _WriteReviewDialog extends ConsumerStatefulWidget {
  final String bookId;
  final String sort;

  const _WriteReviewDialog({required this.bookId, required this.sort});

  @override
  ConsumerState<_WriteReviewDialog> createState() => _WriteReviewDialogState();
}

class _WriteReviewDialogState extends ConsumerState<_WriteReviewDialog> {
  int _rating = 0;
  final _textController = TextEditingController();
  bool _submitting = false;

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Write a Review'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Tap to rate:'),
            const SizedBox(height: 8),
            StarRating(
              rating: _rating.toDouble(),
              size: 36,
              interactive: true,
              onChanged: (v) => setState(() => _rating = v),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _textController,
              maxLines: 4,
              maxLength: 5000,
              decoration: const InputDecoration(
                hintText: 'Write your review (optional)',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _submitting ? null : () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        FilledButton(
          onPressed: _rating == 0 || _submitting ? null : _submit,
          child: _submitting
              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
              : const Text('Submit'),
        ),
      ],
    );
  }

  Future<void> _submit() async {
    setState(() => _submitting = true);
    try {
      final api = ref.read(apiServiceProvider);
      await api.createOrUpdateReview(
        widget.bookId,
        rating: _rating,
        reviewText: _textController.text,
      );
      ref.invalidate(bookReviewsProvider(ReviewsParam(widget.bookId, sort: widget.sort)));
      if (mounted) Navigator.pop(context);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to submit review: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }
}
