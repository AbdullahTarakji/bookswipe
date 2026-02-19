import 'package:flutter/material.dart';

/// A reusable widget that constrains its child to a maximum width and centers it.
///
/// Used across screens for tablet-friendly layouts.
class ResponsiveContainer extends StatelessWidget {
  /// The child widget to constrain.
  final Widget child;

  /// The maximum width to constrain the child to.
  final double maxWidth;

  /// Creates a responsive container with the given [maxWidth].
  const ResponsiveContainer({
    super.key,
    required this.child,
    this.maxWidth = 500,
  });

  /// Whether the current screen width indicates a tablet (>= 600px).
  static bool isTablet(BuildContext context) {
    return MediaQuery.of(context).size.width >= 600;
  }

  @override
  Widget build(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: maxWidth),
        child: child,
      ),
    );
  }
}
