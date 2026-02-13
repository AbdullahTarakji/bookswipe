import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Swipe-style stamp overlay shown during a swipe.
///
/// Renders a rotated bordered "LIKE" (green, top-left) or "NOPE"
/// (red, top-right) stamp whose opacity increases with the drag distance.
class SwipeOverlay extends StatelessWidget {
  final bool isLike;
  final double opacity;

  const SwipeOverlay({
    super.key,
    required this.isLike,
    this.opacity = 1.0,
  });

  @override
  Widget build(BuildContext context) {
    final color = isLike ? AppTheme.likeGreen : AppTheme.nopeRed;
    final label = isLike ? 'LIKE' : 'NOPE';
    final angle = isLike ? -0.4 : 0.4;

    return Positioned(
      top: 50,
      left: isLike ? 24 : null,
      right: isLike ? null : 24,
      child: Opacity(
        opacity: opacity.clamp(0.0, 1.0),
        child: Transform.rotate(
          angle: angle,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              border: Border.all(color: color, width: 4),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              label,
              style: TextStyle(
                color: color,
                fontSize: 48,
                fontWeight: FontWeight.w900,
                letterSpacing: 4,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
