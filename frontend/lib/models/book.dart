/// Represents a book with metadata from Google Books or the backend API.
class Book {
  final String id;
  final String title;
  final List<String> authors;
  final String? description;
  final String? thumbnailUrl;
  final int? pageCount;
  final double? averageRating;
  final int? ratingsCount;
  final List<String> categories;
  final String? publishedDate;
  final String? publisher;
  final String? previewLink;
  final bool isLiked;
  final String? blurhash;
  final String? thumbnailCdn;
  final String? cardCdn;
  final String? detailCdn;

  const Book({
    required this.id,
    required this.title,
    required this.authors,
    this.description,
    this.thumbnailUrl,
    this.pageCount,
    this.averageRating,
    this.ratingsCount,
    this.categories = const [],
    this.publishedDate,
    this.publisher,
    this.previewLink,
    this.isLiked = false,
    this.blurhash,
    this.thumbnailCdn,
    this.cardCdn,
    this.detailCdn,
  });

  String get authorsText => authors.join(', ');

  /// Whether a blurhash placeholder is available for progressive loading.
  bool get hasBlurhash => blurhash != null && blurhash!.isNotEmpty;

  /// Best available cover URL: CDN card size > proxy > raw thumbnail.
  String get highResThumbnail {
    if (cardCdn != null && cardCdn!.isNotEmpty) return cardCdn!;
    if (thumbnailUrl == null || thumbnailUrl!.isEmpty) return '';
    final url = thumbnailUrl!;
    // Proxy URLs are relative — use as-is (same origin)
    if (url.startsWith('/api/')) {
      return url;
    }
    return url;
  }

  /// Detail-quality cover URL for full-screen views.
  String get detailCoverUrl {
    if (detailCdn != null && detailCdn!.isNotEmpty) return detailCdn!;
    return highResThumbnail;
  }

  Book copyWith({
    String? id,
    String? title,
    List<String>? authors,
    String? description,
    String? thumbnailUrl,
    int? pageCount,
    double? averageRating,
    int? ratingsCount,
    List<String>? categories,
    String? publishedDate,
    String? publisher,
    String? previewLink,
    bool? isLiked,
    String? blurhash,
    String? thumbnailCdn,
    String? cardCdn,
    String? detailCdn,
  }) {
    return Book(
      id: id ?? this.id,
      title: title ?? this.title,
      authors: authors ?? this.authors,
      description: description ?? this.description,
      thumbnailUrl: thumbnailUrl ?? this.thumbnailUrl,
      pageCount: pageCount ?? this.pageCount,
      averageRating: averageRating ?? this.averageRating,
      ratingsCount: ratingsCount ?? this.ratingsCount,
      categories: categories ?? this.categories,
      publishedDate: publishedDate ?? this.publishedDate,
      publisher: publisher ?? this.publisher,
      previewLink: previewLink ?? this.previewLink,
      isLiked: isLiked ?? this.isLiked,
      blurhash: blurhash ?? this.blurhash,
      thumbnailCdn: thumbnailCdn ?? this.thumbnailCdn,
      cardCdn: cardCdn ?? this.cardCdn,
      detailCdn: detailCdn ?? this.detailCdn,
    );
  }

  factory Book.fromJson(Map<String, dynamic> json) {
    // Google Books API format (has volumeInfo)
    if (json.containsKey('volumeInfo')) {
      return Book._fromGoogleJson(json);
    }
    // Backend flat format (has google_book_id or flat title field)
    return Book._fromBackendJson(json);
  }

  factory Book._fromBackendJson(Map<String, dynamic> json) {
    // Parse authors: backend discover returns List<String>,
    // but liked books endpoint returns a comma-joined String
    List<String> authors;
    final rawAuthors = json['authors'];
    if (rawAuthors is List) {
      authors = rawAuthors.map((a) => a as String).toList();
    } else if (rawAuthors is String) {
      authors = rawAuthors.split(',').map((a) => a.trim()).where((a) => a.isNotEmpty).toList();
    } else {
      authors = ['Unknown Author'];
    }

    return Book(
      id: json['google_book_id'] as String? ?? json['id'].toString(),
      title: json['title'] as String? ?? 'Unknown Title',
      authors: authors,
      description: json['description'] as String?,
      thumbnailUrl: json['thumbnail'] as String?,
      pageCount: json['page_count'] as int?,
      averageRating: (json['average_rating'] as num?)?.toDouble(),
      ratingsCount: json['ratings_count'] as int?,
      categories: (json['categories'] as List<dynamic>?)
              ?.map((c) => c as String)
              .toList() ??
          [],
      publishedDate: json['published_date'] as String?,
      publisher: json['publisher'] as String?,
      previewLink: json['preview_link'] as String?,
      isLiked: json['is_liked'] as bool? ?? false,
      blurhash: json['blurhash'] as String?,
      thumbnailCdn: json['thumbnail_cdn'] as String?,
      cardCdn: json['card_cdn'] as String?,
      detailCdn: json['detail_cdn'] as String?,
    );
  }

  factory Book._fromGoogleJson(Map<String, dynamic> json) {
    final volumeInfo =
        json['volumeInfo'] as Map<String, dynamic>? ?? {};
    final imageLinks =
        volumeInfo['imageLinks'] as Map<String, dynamic>? ?? {};
    return Book(
      id: json['id'] as String,
      title: volumeInfo['title'] as String? ?? 'Unknown Title',
      authors: (volumeInfo['authors'] as List<dynamic>?)
              ?.map((a) => a as String)
              .toList() ??
          ['Unknown Author'],
      description: volumeInfo['description'] as String?,
      thumbnailUrl:
          (imageLinks['thumbnail'] as String?)?.replaceAll('http://', 'https://'),
      pageCount: volumeInfo['pageCount'] as int?,
      averageRating: (volumeInfo['averageRating'] as num?)?.toDouble(),
      ratingsCount: volumeInfo['ratingsCount'] as int?,
      categories: (volumeInfo['categories'] as List<dynamic>?)
              ?.map((c) => c as String)
              .toList() ??
          [],
      publishedDate: volumeInfo['publishedDate'] as String?,
      publisher: volumeInfo['publisher'] as String?,
      previewLink: volumeInfo['previewLink'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'authors': authors,
      'description': description,
      'thumbnail_url': thumbnailUrl,
      'page_count': pageCount,
      'average_rating': averageRating,
      'ratings_count': ratingsCount,
      'categories': categories,
      'published_date': publishedDate,
      'publisher': publisher,
      'preview_link': previewLink,
      'is_liked': isLiked,
      'blurhash': blurhash,
      'thumbnail_cdn': thumbnailCdn,
      'card_cdn': cardCdn,
      'detail_cdn': detailCdn,
    };
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is Book && id == other.id;

  @override
  int get hashCode => id.hashCode;
}
