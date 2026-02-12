import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';

class MockDioAdapter implements HttpClientAdapter {
  int _statusCode = 200;
  dynamic _responseData;
  Uri? lastRequestUri;
  dynamic lastRequestData;

  void setResponse(int statusCode, dynamic data) {
    _statusCode = statusCode;
    _responseData = data;
  }

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    lastRequestUri = options.uri;
    lastRequestData = options.data;

    final jsonStr = jsonEncode(_responseData);
    return ResponseBody.fromString(
      jsonStr,
      _statusCode,
      headers: {
        Headers.contentTypeHeader: ['application/json'],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}
