/// Represents an authenticated user with their JWT tokens and subscription info.
class User {
  final String id;
  final String email;
  final String token;
  final String refreshToken;
  final String role;
  final String subscriptionStatus;
  final String subscriptionPlan;
  final String? subscriptionEndDate;

  const User({
    required this.id,
    required this.email,
    required this.token,
    this.refreshToken = '',
    this.role = 'user',
    this.subscriptionStatus = 'free',
    this.subscriptionPlan = 'free',
    this.subscriptionEndDate,
  });

  bool get isAdmin => role == 'admin';

  bool get isPremium =>
      subscriptionStatus == 'active' && subscriptionPlan == 'premium';

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: (json['id'] ?? '').toString(),
      email: json['email'] as String? ?? '',
      token: json['token'] as String? ?? json['access_token'] as String? ?? '',
      refreshToken: json['refresh_token'] as String? ?? '',
      role: json['role'] as String? ?? 'user',
      subscriptionStatus:
          json['subscription_status'] as String? ?? 'free',
      subscriptionPlan: json['subscription_plan'] as String? ?? 'free',
      subscriptionEndDate: json['subscription_end_date'] as String?,
    );
  }

  User copyWithTokens({required String token, required String refreshToken}) {
    return User(
      id: id,
      email: email,
      token: token,
      refreshToken: refreshToken,
      role: role,
      subscriptionStatus: subscriptionStatus,
      subscriptionPlan: subscriptionPlan,
      subscriptionEndDate: subscriptionEndDate,
    );
  }

  User copyWithSubscription({
    required String subscriptionStatus,
    required String subscriptionPlan,
    String? subscriptionEndDate,
  }) {
    return User(
      id: id,
      email: email,
      token: token,
      refreshToken: refreshToken,
      role: role,
      subscriptionStatus: subscriptionStatus,
      subscriptionPlan: subscriptionPlan,
      subscriptionEndDate: subscriptionEndDate,
    );
  }

  User copyWith({
    String? id,
    String? email,
    String? token,
    String? refreshToken,
    String? role,
    String? subscriptionStatus,
    String? subscriptionPlan,
    String? subscriptionEndDate,
  }) {
    return User(
      id: id ?? this.id,
      email: email ?? this.email,
      token: token ?? this.token,
      refreshToken: refreshToken ?? this.refreshToken,
      role: role ?? this.role,
      subscriptionStatus: subscriptionStatus ?? this.subscriptionStatus,
      subscriptionPlan: subscriptionPlan ?? this.subscriptionPlan,
      subscriptionEndDate: subscriptionEndDate ?? this.subscriptionEndDate,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'email': email,
        'token': token,
        'refresh_token': refreshToken,
        'role': role,
        'subscription_status': subscriptionStatus,
        'subscription_plan': subscriptionPlan,
        'subscription_end_date': subscriptionEndDate,
      };
}
