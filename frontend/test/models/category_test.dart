import 'package:flutter_test/flutter_test.dart';
import 'package:bookswipe/models/category.dart';

void main() {
  group('BookCategory', () {
    test('defaults contains 14 categories', () {
      expect(BookCategory.defaults.length, 14);
    });

    test('each category has a unique key', () {
      final keys = BookCategory.defaults.map((c) => c.key).toSet();
      expect(keys.length, BookCategory.defaults.length);
    });

    test('each category has a non-empty name', () {
      for (final cat in BookCategory.defaults) {
        expect(cat.name, isNotEmpty);
      }
    });
  });
}
