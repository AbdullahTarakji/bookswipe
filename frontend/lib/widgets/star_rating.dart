import 'package:flutter/material.dart';

/// Interactive or read-only star rating widget.
class StarRating extends StatelessWidget {
  final double rating;
  final double size;
  final bool interactive;
  final ValueChanged<int>? onChanged;
  final Color? color;

  const StarRating({
    super.key,
    required this.rating,
    this.size = 24,
    this.interactive = false,
    this.onChanged,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    final starColor = color ?? Theme.of(context).colorScheme.primary;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(5, (index) {
        final starValue = index + 1;
        IconData icon;
        if (rating >= starValue) {
          icon = Icons.star;
        } else if (rating >= starValue - 0.5) {
          icon = Icons.star_half;
        } else {
          icon = Icons.star_border;
        }
        if (interactive) {
          return GestureDetector(
            onTap: () => onChanged?.call(starValue),
            child: Icon(icon, size: size, color: starColor),
          );
        }
        return Icon(icon, size: size, color: starColor);
      }),
    );
  }
}
