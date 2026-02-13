import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:bookswipe/screens/user_search_screen.dart';

void main() {
  group('UserSearchScreen', () {
    testWidgets('renders with search field', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: UserSearchScreen(),
          ),
        ),
      );

      expect(find.text('Find People'), findsOneWidget);
      expect(find.byType(TextField), findsOneWidget);
      expect(find.text('Search for people'), findsOneWidget);
    });
  });
}
