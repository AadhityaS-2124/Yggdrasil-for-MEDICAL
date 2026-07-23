/// Riverpod state management for the query lifecycle.
///
/// Explicit states:
///   - idle: no query in progress
///   - loading_step_1: "Dissecting language..."
///   - loading_step_2: "Searching Neurology Index..."
///   - loading_step_3: "Calculating probability..."
///   - success: backend returned OK with candidates
///   - noVerifiedData: backend returned NO_VERIFIED_DATA
///   - error: HTTP error or network failure
///
/// The loading steps are cosmetic pacing — main.py returns one response
/// at the end, so we time-slice the perceived wait to match the master
/// plan's "[Step 1/3...]" indicator spec.

import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/disease_node.dart';
import '../services/api_client.dart';

// ---------------------------------------------------------------------------
// State definition
// ---------------------------------------------------------------------------

enum QueryPhase {
  idle,
  loadingStep1, // "Dissecting language..."
  loadingStep2, // "Searching Neurology Index..."
  loadingStep3, // "Calculating probability..."
  success,
  noVerifiedData,
  error,
}

class QueryState {
  final QueryPhase phase;
  final AnalyzeResponse? response;
  final String? errorMessage;
  final String? noDataReason;

  const QueryState({
    this.phase = QueryPhase.idle,
    this.response,
    this.errorMessage,
    this.noDataReason,
  });

  bool get isLoading =>
      phase == QueryPhase.loadingStep1 ||
      phase == QueryPhase.loadingStep2 ||
      phase == QueryPhase.loadingStep3;

  String get loadingMessage {
    switch (phase) {
      case QueryPhase.loadingStep1:
        return '[Step 1/3: Dissecting language...]';
      case QueryPhase.loadingStep2:
        return '[Step 2/3: Searching Neurology Index...]';
      case QueryPhase.loadingStep3:
        return '[Step 3/3: Calculating probability...]';
      default:
        return '';
    }
  }
}

// ---------------------------------------------------------------------------
// Step durations for cosmetic pacing (milliseconds)
// ---------------------------------------------------------------------------
const _step1Duration = Duration(milliseconds: 800);
const _step2Duration = Duration(milliseconds: 1200);

// ---------------------------------------------------------------------------
// Notifier (Riverpod 3.x Notifier API)
// ---------------------------------------------------------------------------

class QueryNotifier extends Notifier<QueryState> {
  ApiClient? _overrideClient;

  QueryNotifier({ApiClient? apiClient}) : _overrideClient = apiClient;

  ApiClient get _apiClient => _overrideClient ?? ApiClient();

  @override
  QueryState build() => const QueryState();

  Future<void> submit(String text) async {
    // Start loading sequence
    state = const QueryState(phase: QueryPhase.loadingStep1);

    // Fire API call immediately, but pace the UI steps.
    // Store any error so it doesn't go unhandled during the delay steps.
    AnalyzeResponse? apiResult;
    Object? apiError;

    _apiClient.analyze(text).then((result) {
      apiResult = result;
    }).catchError((Object error) {
      apiError = error;
    });

    // Step 1 → Step 2 after delay
    await Future.delayed(_step1Duration);
    if (state.phase == QueryPhase.loadingStep1) {
      state = const QueryState(phase: QueryPhase.loadingStep2);
    }

    // Step 2 → Step 3 after delay
    await Future.delayed(_step2Duration);
    if (state.phase == QueryPhase.loadingStep2) {
      state = const QueryState(phase: QueryPhase.loadingStep3);
    }

    // If API hasn't finished yet, wait for it with a polling loop
    while (apiResult == null && apiError == null) {
      await Future.delayed(const Duration(milliseconds: 100));
    }

    // Handle result
    if (apiError != null) {
      final error = apiError!;
      if (error is ApiException) {
        state = QueryState(
          phase: QueryPhase.error,
          errorMessage: error.message,
        );
      } else {
        state = QueryState(
          phase: QueryPhase.error,
          errorMessage: 'Unexpected error: $error',
        );
      }
      return;
    }

    final response = apiResult!;
    if (response.isOk) {
      state = QueryState(
        phase: QueryPhase.success,
        response: response,
      );
    } else if (response.isNoVerifiedData) {
      state = QueryState(
        phase: QueryPhase.noVerifiedData,
        noDataReason: response.reason,
        response: response,
      );
    } else {
      state = QueryState(
        phase: QueryPhase.error,
        errorMessage: 'Unexpected status: ${response.status}',
      );
    }
  }

  void reset() {
    state = const QueryState();
  }
}

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

final queryProvider = NotifierProvider<QueryNotifier, QueryState>(() {
  return QueryNotifier();
});
