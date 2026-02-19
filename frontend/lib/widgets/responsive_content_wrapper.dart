import 'package:flutter/material.dart';
import '../utils/responsive_utils.dart';

class ResponsiveContentWrapper extends StatelessWidget {
  final Widget child;

  const ResponsiveContentWrapper({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: BoxConstraints(
          maxWidth: maxContentWidth(context),
        ),
        child: child,
      ),
    );
  }
}
