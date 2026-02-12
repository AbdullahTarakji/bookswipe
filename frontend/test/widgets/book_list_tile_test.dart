import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:bookswipe/models/book.dart';
import 'package:bookswipe/widgets/book_list_tile.dart';

void main() {
  group('BookListTile', () {
    testWidgets('displays book title and author', (tester) async {
      const book = Book(
        id: '1',
        title: 'Test Book',
        authors: ['Jane Doe'],
        thumbnailUrl: null,
      );

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: BookListTile(book: book)),
        ),
      );

      expect(find.text('Test Book'), findsOneWidget);
      expect(find.text('Jane Doe'), findsOneWidget);
    });

    testWidgets('shows rating badge when available', (tester) async {
      const book = Book(
        id: '1',
        title: 'Rated Book',
        authors: ['Author'],
        averageRating: 3.8,
        thumbnailUrl: null,
      );

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: BookListTile(book: book)),
        ),
      );

      expect(find.text('3.8'), findsOneWidget);
      expect(find.byIcon(Icons.star_rounded), findsOneWidget);
    });

    testWidgets('hides rating badge when no rating', (tester) async {
      const book = Book(
        id: '1',
        title: 'Unrated Book',
        authors: ['Author'],
        thumbnailUrl: null,
      );

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: BookListTile(book: book)),
        ),
      );

      expect(find.byIcon(Icons.star_rounded), findsNothing);
    });

    testWidgets('calls onTap callback', (tester) async {
      var tapped = false;
      const book = Book(
        id: '1',
        title: 'Tappable',
        authors: ['Author'],
        thumbnailUrl: null,
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: BookListTile(book: book, onTap: () => tapped = true),
          ),
        ),
      );

      await tester.tap(find.text('Tappable'));
      expect(tapped, isTrue);
    });

    testWidgets('is dismissible when onDismiss provided', (tester) async {
      var dismissed = false;
      const book = Book(
        id: '1',
        title: 'Dismissible Book',
        authors: ['Author'],
        thumbnailUrl: null,
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: BookListTile(
              book: book,
              onDismiss: () => dismissed = true,
            ),
          ),
        ),
      );

      expect(find.byType(Dismissible), findsOneWidget);

      // Swipe to dismiss
      await tester.drag(find.text('Dismissible Book'), const Offset(-500, 0));
      await tester.pumpAndSettle();

      expect(dismissed, isTrue);
    });

    testWidgets('is not dismissible when onDismiss is null', (tester) async {
      const book = Book(
        id: '1',
        title: 'Non-dismissible',
        authors: ['Author'],
        thumbnailUrl: null,
      );

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: BookListTile(book: book)),
        ),
      );

      expect(find.byType(Dismissible), findsNothing);
    });

    testWidgets('shows placeholder for book without thumbnail', (tester) async {
      const book = Book(
        id: '1',
        title: 'No Thumb',
        authors: ['Author'],
        thumbnailUrl: null,
      );

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: BookListTile(book: book)),
        ),
      );

      expect(find.byIcon(Icons.book), findsOneWidget);
    });
  });
}
