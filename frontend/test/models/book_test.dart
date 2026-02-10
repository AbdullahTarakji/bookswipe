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

    test('fromJson parses backend format with volume_info', () {
      final json = {
        'id': 'xyz789',
        'google_book_id': 'xyz789',
        'volume_info': {
          'title': 'Backend Book',
          'authors': ['Jane Doe'],
          'description': 'From backend.',
          'thumbnail_url': 'https://example.com/cover.jpg',
          'page_count': 200,
          'average_rating': 3.8,
          'ratings_count': 50,
          'categories': ['Science'],
          'published_date': '2022-06-15',
          'publisher': 'Backend Press',
          'preview_link': 'https://example.com/preview',
        },
        'is_liked': true,
      };

      final book = Book.fromJson(json);

      expect(book.id, 'xyz789');
      expect(book.title, 'Backend Book');
      expect(book.authors, ['Jane Doe']);
      expect(book.isLiked, true);
      expect(book.pageCount, 200);
      expect(book.averageRating, 3.8);
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

    test('highResThumbnail replaces zoom parameter', () {
      const book = Book(
        id: '1',
        title: 'Test',
        authors: [],
        thumbnailUrl: 'https://books.google.com/thumb?zoom=1',
      );

      expect(book.highResThumbnail, contains('zoom=2'));
      expect(book.highResThumbnail, isNot(contains('zoom=1')));
    });
  });
}
