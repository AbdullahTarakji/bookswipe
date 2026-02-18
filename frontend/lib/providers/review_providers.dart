import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'providers.dart';

/// Parameter for fetching reviews: book ID + sort option.
class ReviewsParam {
  final String bookId;
  final String sort;

  const ReviewsParam(this.bookId, {this.sort = 'newest'});

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is ReviewsParam && bookId == other.bookId && sort == other.sort;

  @override
  int get hashCode => bookId.hashCode ^ sort.hashCode;
}

/// Provides paginated reviews for a book.
final bookReviewsProvider =
    FutureProvider.family<Map<String, dynamic>, ReviewsParam>((ref, param) async {
  final api = ref.read(apiServiceProvider);
  return api.getBookReviews(param.bookId, sort: param.sort);
});
