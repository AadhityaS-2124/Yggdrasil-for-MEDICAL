/// API client for the FastAPI backend at localhost:8008.
///
/// Handles all three response shapes explicitly:
///   - "OK" with candidates
///   - "NO_VERIFIED_DATA" (empty parse or no matching diseases)
///   - HTTP errors (400/422/500)

import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/disease_node.dart';

/// Exception thrown when the backend returns an HTTP error.
class ApiException implements Exception {
  final int statusCode;
  final String message;

  const ApiException({required this.statusCode, required this.message});

  @override
  String toString() => 'ApiException($statusCode): $message';
}

class ApiClient {
  final String baseUrl;
  final http.Client _client;

  ApiClient({
    this.baseUrl = 'http://localhost:8008',
    http.Client? client,
  }) : _client = client ?? http.Client();

  /// POST /analyze with the user's natural language text.
  ///
  /// Returns [AnalyzeResponse] for both OK and NO_VERIFIED_DATA cases.
  /// Throws [ApiException] for HTTP errors (400/422/500/network failures).
  Future<AnalyzeResponse> analyze(String text) async {
    final uri = Uri.parse('$baseUrl/analyze');

    final http.Response response;
    try {
      response = await _client.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'text': text}),
      );
    } catch (e) {
      throw ApiException(
        statusCode: 0,
        message: 'Network error: could not reach backend at $baseUrl. '
            'Is the FastAPI server running? ($e)',
      );
    }

    if (response.statusCode == 200) {
      final json = jsonDecode(response.body) as Map<String, dynamic>;
      return AnalyzeResponse.fromJson(json);
    }

    // Extract error detail from FastAPI's error response format
    String detail;
    try {
      final errorJson = jsonDecode(response.body) as Map<String, dynamic>;
      detail = errorJson['detail']?.toString() ?? response.body;
    } catch (_) {
      detail = response.body;
    }

    throw ApiException(
      statusCode: response.statusCode,
      message: detail,
    );
  }

  void dispose() {
    _client.close();
  }
}
