import 'package:flutter_test/flutter_test.dart';
import 'package:bookswipe/models/book.dart';

void main() {
  group('Book', () {
    test('fromJson parses Google Books API format', () {
      final json = {
        'id': 'abc123',
        'volumeInfo': {
          'title': 'Test Book',
          'authors': ['Author One', 'Author Two'],
          'description': 'A great book.',
          'pageCount': 300,
          'averageRating': 4.5,
          'ratingsCount': 100,
          'categories': ['Fiction'],
          'publishedDate': '2023-01-01',
          'publisher': 'Test Publisher',
          'previewLink': 'https://books.google.com/test',
          'imageLinks': {
            'thumbnail': 'http://books.google.com/thumb.jpg',
          },
        },
      };

      final book = Book.fromJson(json);

      expect(book.id, 'abc123');
      expect(book.title, 'Test Book');
      expect(book.authors, ['Author One', 'Author Two']);
      expect(book.authorsText, 'Author One, Author Two');
      expect(book.description, 'A great book.');
      expect(book.pageCount, 300);
      expect(book.averageRating, 4.5);
      expect(book.ratingsCount, 100);
      expect(book.categories, ['Fiction']);
      expect(book.publishedDate, '2023-01-01');
      expect(book.publisher, 'Test Publisher');
      expect(book.thumbnailUrl, 'https://books.google.com/thumb.jpg');
    });

    test('fromJson parses flat backend format from discover endpoint', () {
      final json = {
        'google_book_id': 'xyz789',
        'title': 'Backend Book',
        'authors': ['Jane Doe'],
        'thumbnail': 'https://example.com/cover.jpg',
        'categories': ['Science'],
        'average_rating': 3.8,
        'ratings_count': 50,
      };

      final book = Book.fromJson(json);

      expect(book.id, 'xyz789');
      expect(book.title, 'Backend Book');
      expect(book.authors, ['Jane Doe']);
      expect(book.thumbnailUrl, 'https://example.com/cover.jpg');
      expect(book.categories, ['Science']);
      expect(book.averageRating, 3.8);
      expect(book.ratingsCount, 50);
    });

    test('fromJson parses liked books with authors as string', () {
      final json = {
        'id': 1,
        'google_book_id': 'abc123',
        'title': 'Liked Book',
        'authors': 'Author One, Author Two',
        'thumbnail': 'https://example.com/thumb.jpg',
        'liked_at': '2024-01-01T00:00:00',
      };

      final book = Book.fromJson(json);

      expect(book.id, 'abc123');
      expect(book.title, 'Liked Book');
      expect(book.authors, ['Author One', 'Author Two']);
      expect(book.thumbnailUrl, 'https://example.com/thumb.jpg');
    });

    test('fromJson parses backend book detail format', () {
      final json = {
        'google_book_id': 'detail123',
        'title': 'Detailed Book',
        'authors': ['Author A', 'Author B'],
        'thumbnail': 'https://example.com/detail.jpg',
        'description': 'A detailed description.',
        'page_count': 350,
        'average_rating': 4.2,
        'ratings_count': 200,
        'categories': ['Fiction', 'Adventure'],
      };

      final book = Book.fromJson(json);

      expect(book.id, 'detail123');
      expect(book.title, 'Detailed Book');
      expect(book.authors, ['Author A', 'Author B']);
      expect(book.description, 'A detailed description.');
      expect(book.pageCount, 350);
      expect(book.averageRating, 4.2);
      expect(book.ratingsCount, 200);
      expect(book.categories, ['Fiction', 'Adventure']);
    });

    test('fromJson handles missing fields gracefully', () {
      final json = {
        'id': 'minimal',
        'volumeInfo': <String, dynamic>{},
      };

      final book = Book.fromJson(json);

      expect(book.id, 'minimal');
      expect(book.title, 'Unknown Title');
      expect(book.authors, ['Unknown Author']);
      expect(book.description, isNull);
      expect(book.thumbnailUrl, isNull);
      expect(book.pageCount, isNull);
      expect(book.averageRating, isNull);
    });

    test('copyWith creates modified copy', () {
      const book = Book(
        id: '1',
        title: 'Original',
        authors: ['Author'],
      );

      final liked = book.copyWith(isLiked: true);

      expect(liked.id, '1');
      expect(liked.title, 'Original');
      expect(liked.isLiked, true);
      expect(book.isLiked, false);
    });

    test('equality based on id', () {
      const book1 = Book(id: '1', title: 'A', authors: ['X']);
      const book2 = Book(id: '1', title: 'B', authors: ['Y']);
      const book3 = Book(id: '2', title: 'A', authors: ['X']);

      expect(book1, equals(book2));
      expect(book1, isNot(equals(book3)));
    });

    test('toJson serializes correctly', () {
      const book = Book(
        id: '1',
        title: 'Test',
        authors: ['Auth'],
        pageCount: 100,
        isLiked: true,
      );

      final json = book.toJson();

      expect(json['id'], '1');
      expect(json['title'], 'Test');
      expect(json['authors'], ['Auth']);
      expect(json['page_count'], 100);
      expect(json['is_liked'], true);
    });

    test('highResThumbnail returns url as-is', () {
      const book = Book(
        id: '1',
        title: 'Test',
        authors: [],
        thumbnailUrl: 'https://books.google.com/thumb?zoom=1',
      );

      expect(book.highResThumbnail, 'https://books.google.com/thumb?zoom=1');
    });
  });
}
