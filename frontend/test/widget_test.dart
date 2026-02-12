import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:bookswipe/widgets/error_view.dart';
import 'package:bookswipe/widgets/loading_indicator.dart';

void main() {
  group('LoadingIndicator', () {
    testWidgets('shows progress indicator', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: LoadingIndicator()),
        ),
      );

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('shows message when provided', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: LoadingIndicator(message: 'Loading...')),
        ),
      );

      expect(find.text('Loading...'), findsOneWidget);
    });
  });

  group('ErrorView', () {
    testWidgets('shows error message', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: ErrorView(message: 'Something went wrong')),
        ),
      );

      expect(find.text('Something went wrong'), findsOneWidget);
      expect(find.byIcon(Icons.cloud_off_rounded), findsOneWidget);
    });

    testWidgets('shows retry button when callback provided', (tester) async {
      var retried = false;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ErrorView(
              message: 'Error',
              onRetry: () => retried = true,
            ),
          ),
        ),
      );

      expect(find.text('Try Again'), findsOneWidget);
      await tester.tap(find.text('Try Again'));
      expect(retried, true);
    });

    testWidgets('hides retry button when no callback', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: ErrorView(message: 'Error')),
        ),
      );

      expect(find.text('Try Again'), findsNothing);
    });

    testWidgets('shows default title', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: ErrorView(message: 'Error')),
        ),
      );

      expect(find.text('Oops!'), findsOneWidget);
    });

    testWidgets('shows custom title and icon', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: ErrorView(
              message: 'Not found',
              title: 'Missing',
              icon: Icons.search_off,
            ),
          ),
        ),
      );

      expect(find.text('Missing'), findsOneWidget);
      expect(find.byIcon(Icons.search_off), findsOneWidget);
    });
  });
}
