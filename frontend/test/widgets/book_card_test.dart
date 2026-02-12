import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:bookswipe/models/book.dart';
import 'package:bookswipe/widgets/book_card.dart';

void main() {
  group('BookCard', () {
    testWidgets('displays book title and author', (tester) async {
      const book = Book(
        id: '1',
        title: 'Test Book Title',
        authors: ['Author One', 'Author Two'],
        thumbnailUrl: null,
      );

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: SizedBox(width: 300, height: 500, child: BookCard(book: book))),
        ),
      );

      expect(find.text('Test Book Title'), findsOneWidget);
      expect(find.text('Author One, Author Two'), findsOneWidget);
    });

    testWidgets('shows rating when available', (tester) async {
      const book = Book(
        id: '1',
        title: 'Rated Book',
        authors: ['Author'],
        averageRating: 4.5,
        categories: ['Fiction'],
        thumbnailUrl: null,
      );

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: SizedBox(width: 300, height: 500, child: BookCard(book: book))),
        ),
      );

      expect(find.text('4.5'), findsOneWidget);
      expect(find.byIcon(Icons.star_rounded), findsOneWidget);
    });

    testWidgets('shows category badge', (tester) async {
      const book = Book(
        id: '1',
        title: 'Categorized Book',
        authors: ['Author'],
        categories: ['Science Fiction'],
        thumbnailUrl: null,
      );

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: SizedBox(width: 300, height: 500, child: BookCard(book: book))),
        ),
      );

      expect(find.text('Science Fiction'), findsOneWidget);
    });

    testWidgets('calls onTap callback', (tester) async {
      var tapped = false;
      const book = Book(
        id: '1',
        title: 'Tappable Book',
        authors: ['Author'],
        thumbnailUrl: null,
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SizedBox(
              width: 300,
              height: 500,
              child: BookCard(book: book, onTap: () => tapped = true),
            ),
          ),
        ),
      );

      await tester.tap(find.byType(BookCard));
      expect(tapped, isTrue);
    });

    testWidgets('shows placeholder icon when no thumbnail', (tester) async {
      const book = Book(
        id: '1',
        title: 'No Image',
        authors: ['Author'],
        thumbnailUrl: null,
      );

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: SizedBox(width: 300, height: 500, child: BookCard(book: book))),
        ),
      );

      expect(find.byIcon(Icons.menu_book_rounded), findsOneWidget);
    });

    testWidgets('shows info icon hint', (tester) async {
      const book = Book(
        id: '1',
        title: 'Info Book',
        authors: ['Author'],
        thumbnailUrl: null,
      );

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: SizedBox(width: 300, height: 500, child: BookCard(book: book))),
        ),
      );

      expect(find.byIcon(Icons.info_outline), findsOneWidget);
    });
  });
}
