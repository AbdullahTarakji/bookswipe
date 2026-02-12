/// Represents an authenticated user with their JWT tokens and subscription info.
class User {
  final String id;
  final String email;
  final String token;
  final String refreshToken;
  final String subscriptionStatus;
  final String subscriptionPlan;
  final String? subscriptionEndDate;

  const User({
    required this.id,
    required this.email,
    required this.token,
    this.refreshToken = '',
    this.subscriptionStatus = 'free',
    this.subscriptionPlan = 'free',
    this.subscriptionEndDate,
  });

  bool get isPremium =>
      subscriptionStatus == 'active' && subscriptionPlan == 'premium';

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: (json['id'] ?? '').toString(),
      email: json['email'] as String? ?? '',
      token: json['token'] as String? ?? json['access_token'] as String? ?? '',
      refreshToken: json['refresh_token'] as String? ?? '',
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
      subscriptionStatus: subscriptionStatus,
      subscriptionPlan: subscriptionPlan,
      subscriptionEndDate: subscriptionEndDate,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'email': email,
        'token': token,
        'refresh_token': refreshToken,
        'subscription_status': subscriptionStatus,
        'subscription_plan': subscriptionPlan,
        'subscription_end_date': subscriptionEndDate,
      };
}
