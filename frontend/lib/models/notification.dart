/// A notification record from the user's notification history.
class AppNotification {
  final int id;
  final String title;
  final String body;
  final String category;
  final String? deepLink;
  final bool isRead;
  final DateTime createdAt;

  const AppNotification({
    required this.id,
    required this.title,
    required this.body,
    this.category = 'general',
    this.deepLink,
    this.isRead = false,
    required this.createdAt,
  });

  /// Parse a notification from the API JSON response.
  factory AppNotification.fromJson(Map<String, dynamic> json) {
    return AppNotification(
      id: json['id'] as int,
      title: json['title'] as String,
      body: json['body'] as String,
      category: json['category'] as String? ?? 'general',
      deepLink: json['deep_link'] as String?,
      isRead: json['is_read'] as bool? ?? false,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  /// Create a copy with the given fields replaced.
  AppNotification copyWith({bool? isRead}) {
    return AppNotification(
      id: id,
      title: title,
      body: body,
      category: category,
      deepLink: deepLink,
      isRead: isRead ?? this.isRead,
      createdAt: createdAt,
    );
  }
}

/// User preferences for notification categories.
class NotificationPreferences {
  final bool recommendations;
  final bool social;
  final bool marketing;

  const NotificationPreferences({
    this.recommendations = true,
    this.social = true,
    this.marketing = false,
  });

  /// Parse preferences from the API JSON response.
  factory NotificationPreferences.fromJson(Map<String, dynamic> json) {
    return NotificationPreferences(
      recommendations: json['recommendations'] as bool? ?? true,
      social: json['social'] as bool? ?? true,
      marketing: json['marketing'] as bool? ?? false,
    );
  }

  /// Create a copy with the given fields replaced.
  NotificationPreferences copyWith({
    bool? recommendations,
    bool? social,
    bool? marketing,
  }) {
    return NotificationPreferences(
      recommendations: recommendations ?? this.recommendations,
      social: social ?? this.social,
      marketing: marketing ?? this.marketing,
    );
  }
}
