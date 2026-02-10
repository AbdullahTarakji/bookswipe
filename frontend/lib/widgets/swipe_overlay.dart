import 'package:flutter/material.dart';

class SwipeOverlay extends StatelessWidget {
  final bool isLike;

  const SwipeOverlay({super.key, required this.isLike});

  @override
  Widget build(BuildContext context) {
    return Positioned.fill(
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isLike ? Colors.green : Colors.red,
            width: 4,
          ),
        ),
        child: Center(
          child: Transform.rotate(
            angle: isLike ? -0.3 : 0.3,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
              decoration: BoxDecoration(
                border: Border.all(
                  color: isLike ? Colors.green : Colors.red,
                  width: 3,
                ),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                isLike ? 'LIKE' : 'SKIP',
                style: TextStyle(
                  color: isLike ? Colors.green : Colors.red,
                  fontSize: 40,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
