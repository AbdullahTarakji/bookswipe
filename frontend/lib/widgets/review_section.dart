import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';
import '../providers/providers.dart';
import 'star_rating.dart';

/// Displays reviews for a book with write/edit functionality.
class ReviewSection extends ConsumerStatefulWidget {
  final String bookId;

  const ReviewSection({super.key, required this.bookId});

  @override
  ConsumerState<ReviewSection> createState() => _ReviewSectionState();
}

class _ReviewSectionState extends ConsumerState<ReviewSection> {
  Map<String, dynamic>? _reviewsData;
  bool _loading = true;
  String _sortBy = 'newest';

  @override
  void initState() {
    super.initState();
    _loadReviews();
  }

  Future<void> _loadReviews() async {
    setState(() => _loading = true);
    try {
      final api = ref.read(apiServiceProvider);
      final data = await api.getBookReviews(widget.bookId, sortBy: _sortBy);
      if (mounted) setState(() { _reviewsData = data; _loading = false; });
    } catch (e) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _showWriteReviewDialog() async {
    int selectedRating = 0;
    final textController = TextEditingController();

    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Write a Review'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              StarRating(
                rating: selectedRating,
                interactive: true,
                size: 36,
                onChanged: (r) => setDialogState(() => selectedRating = r),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: textController,
                maxLines: 4,
                maxLength: 5000,
                decoration: const InputDecoration(
                  hintText: 'Share your thoughts about this book...',
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
            FilledButton(
              onPressed: selectedRating > 0
                  ? () => Navigator.pop(context, {'rating': selectedRating, 'text': textController.text})
                  : null,
              child: const Text('Submit'),
            ),
          ],
        ),
      ),
    );

    if (result != null) {
      try {
        final api = ref.read(apiServiceProvider);
        await api.createReview(widget.bookId, rating: result['rating'], reviewText: result['text'] ?? '');
        _loadReviews();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Review submitted!')));
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to submit review: $e')));
        }
      }
    }
  }

  Future<void> _toggleVote(int reviewId, bool hasVoted) async {
    try {
      final api = ref.read(apiServiceProvider);
      if (hasVoted) {
        await api.removeVoteReview(reviewId);
      } else {
        await api.voteReview(reviewId);
      }
      _loadReviews();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('Reviews', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
            FilledButton.tonalIcon(
              onPressed: _showWriteReviewDialog,
              icon: const Icon(Icons.rate_review, size: 18),
              label: const Text('Write Review'),
            ),
          ],
        ),
        const SizedBox(height: 8),

        // Average rating summary
        if (_reviewsData != null && _reviewsData!['average_rating'] != null) ...[
          AverageStarRating(
            rating: (_reviewsData!['average_rating'] as num).toDouble(),
            totalRatings: _reviewsData!['total_ratings'] as int? ?? 0,
          ),
          const SizedBox(height: 12),
        ],

        // Sort toggle
        Row(
          children: [
            ChoiceChip(
              label: const Text('Newest'),
              selected: _sortBy == 'newest',
              onSelected: (_) { setState(() => _sortBy = 'newest'); _loadReviews(); },
            ),
            const SizedBox(width: 8),
            ChoiceChip(
              label: const Text('Most Helpful'),
              selected: _sortBy == 'helpful',
              onSelected: (_) { setState(() => _sortBy = 'helpful'); _loadReviews(); },
            ),
          ],
        ),
        const SizedBox(height: 12),

        if (_loading)
          const Center(child: CircularProgressIndicator())
        else if (_reviewsData == null || (_reviewsData!['reviews'] as List).isEmpty)
          Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Text('No reviews yet. Be the first!', style: theme.textTheme.bodyMedium),
            ),
          )
        else
          ...(_reviewsData!['reviews'] as List).map((r) => _buildReviewCard(r, theme)),
      ],
    );
  }

  Widget _buildReviewCard(Map<String, dynamic> review, ThemeData theme) {
    final hasVoted = review['user_has_voted'] as bool? ?? false;
    final helpfulCount = review['helpful_count'] as int? ?? 0;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  radius: 16,
                  child: Text((review['username'] as String? ?? '?')[0].toUpperCase()),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(review['username'] as String? ?? 'Anonymous', style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.bold)),
                      StarRating(rating: review['rating'] as int? ?? 0, size: 16),
                    ],
                  ),
                ),
              ],
            ),
            if ((review['review_text'] as String?)?.isNotEmpty == true) ...[
              const SizedBox(height: 8),
              Text(review['review_text'] as String, style: theme.textTheme.bodyMedium),
            ],
            const SizedBox(height: 8),
            Row(
              children: [
                TextButton.icon(
                  onPressed: () => _toggleVote(review['id'] as int, hasVoted),
                  icon: Icon(
                    hasVoted ? Icons.thumb_up : Icons.thumb_up_outlined,
                    size: 16,
                  ),
                  label: Text('Helpful${helpfulCount > 0 ? ' ($helpfulCount)' : ''}'),
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
}
