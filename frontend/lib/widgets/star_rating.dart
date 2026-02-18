import 'package:flutter/material.dart';

/// Interactive star rating widget.
class StarRating extends StatelessWidget {
  final int rating;
  final int maxRating;
  final double size;
  final bool interactive;
  final ValueChanged<int>? onChanged;

  const StarRating({
    super.key,
    required this.rating,
    this.maxRating = 5,
    this.size = 28,
    this.interactive = false,
    this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(maxRating, (index) {
        final starIndex = index + 1;
        return GestureDetector(
          onTap: interactive ? () => onChanged?.call(starIndex) : null,
          child: Icon(
            starIndex <= rating ? Icons.star : Icons.star_border,
            color: const Color(0xFFFFC107),
            size: size,
          ),
        );
      }),
    );
  }
}

/// Displays an average rating as filled/half/empty stars.
class AverageStarRating extends StatelessWidget {
  final double rating;
  final int totalRatings;
  final double size;

  const AverageStarRating({
    super.key,
    required this.rating,
    this.totalRatings = 0,
    this.size = 18,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        ...List.generate(5, (index) {
          final starIndex = index + 1;
          if (rating >= starIndex) {
            return Icon(Icons.star, color: const Color(0xFFFFC107), size: size);
          } else if (rating >= starIndex - 0.5) {
            return Icon(Icons.star_half, color: const Color(0xFFFFC107), size: size);
          } else {
            return Icon(Icons.star_border, color: const Color(0xFFFFC107), size: size);
          }
        }),
        const SizedBox(width: 4),
        Text(
          rating.toStringAsFixed(1),
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.bold),
        ),
        if (totalRatings > 0) ...[
          const SizedBox(width: 4),
          Text(
            '($totalRatings)',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ],
    );
  }
}
