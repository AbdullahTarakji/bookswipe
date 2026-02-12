/// Represents an authenticated user with their JWT tokens.
class User {
  final String id;
  final String email;
  final String token;
  final String refreshToken;

  const User({
    required this.id,
    required this.email,
    required this.token,
    this.refreshToken = '',
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: (json['id'] ?? '').toString(),
      email: json['email'] as String? ?? '',
      token: json['token'] as String? ?? json['access_token'] as String? ?? '',
      refreshToken: json['refresh_token'] as String? ?? '',
    );
  }

  User copyWithTokens({required String token, required String refreshToken}) {
    return User(
      id: id,
      email: email,
      token: token,
      refreshToken: refreshToken,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'email': email,
        'token': token,
        'refresh_token': refreshToken,
      };
}
