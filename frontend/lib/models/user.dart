class User {
  final String id;
  final String email;
  final String token;

  const User({
    required this.id,
    required this.email,
    required this.token,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as String? ?? '',
      email: json['email'] as String,
      token: json['token'] as String? ?? json['access_token'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'email': email,
        'token': token,
      };
}
