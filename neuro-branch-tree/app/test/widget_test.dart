/// Widget tests for the query lifecycle.
///
/// Tests use a mocked ApiClient to confirm:
///   1. Submitting text triggers loading state
///   2. Mocked OK response → success state with correct data
///   3. Mocked NO_VERIFIED_DATA → noVerifiedData state
///   4. Mocked API error → error state with message

import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:neuro_branch_tree/models/disease_node.dart';
import 'package:neuro_branch_tree/state/query_provider.dart';
import 'package:neuro_branch_tree/services/api_client.dart';

// ---------------------------------------------------------------------------
// Mock API client
// ---------------------------------------------------------------------------

class MockApiClient extends ApiClient {
  final AnalyzeResponse? mockResponse;
  final ApiException? mockError;
  bool analyzeCalled = false;
  String? lastText;

  MockApiClient({this.mockResponse, this.mockError}) : super(baseUrl: 'http://mock');

  @override
  Future<AnalyzeResponse> analyze(String text) async {
    analyzeCalled = true;
    lastText = text;
    if (mockError != null) throw mockError!;
    return mockResponse!;
  }
}

// ---------------------------------------------------------------------------
// Helper: create a container with a mocked QueryNotifier
// ---------------------------------------------------------------------------

ProviderContainer createContainer(MockApiClient mockClient) {
  final container = ProviderContainer(
    overrides: [
      queryProvider.overrideWith(() => QueryNotifier(apiClient: mockClient)),
    ],
  );
  // Read once to initialize
  container.read(queryProvider);
  return container;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

void main() {
  group('QueryNotifier state transitions', () {
    test('starts in idle state', () {
      final mockClient = MockApiClient(
        mockResponse: const AnalyzeResponse(status: 'OK'),
      );
      final container = createContainer(mockClient);

      expect(container.read(queryProvider).phase, QueryPhase.idle);
      container.dispose();
    });

    test('submit triggers loading then success on OK response', () async {
      final mockClient = MockApiClient(
        mockResponse: AnalyzeResponse(
          status: 'OK',
          extractedSymptoms: const ['resting_tremor', 'bradykinesia', 'rigidity'],
          candidates: [
            CandidateNode(
              diseaseId: 'parkinsons_disease',
              namePlain: "Parkinson's Disease",
              confidencePct: 88,
              clinicalReviewStatus: 'unreviewed',
            ),
          ],
        ),
      );
      final container = createContainer(mockClient);
      final notifier = container.read(queryProvider.notifier);

      // Collect phases
      final phases = <QueryPhase>[];
      container.listen(queryProvider, (prev, next) {
        phases.add(next.phase);
      });

      await notifier.submit('shaking at rest, slow movement, stiff arms');

      // Must have passed through loading steps
      expect(phases, contains(QueryPhase.loadingStep1));

      // Final state must be success
      final finalState = container.read(queryProvider);
      expect(finalState.phase, QueryPhase.success);
      expect(finalState.response!.isOk, true);
      expect(finalState.response!.candidates.length, 1);
      expect(finalState.response!.candidates[0].diseaseId, 'parkinsons_disease');
      expect(finalState.response!.candidates[0].confidencePct, 88);
      expect(finalState.response!.candidates[0].clinicalReviewStatus, 'unreviewed');

      // API was called
      expect(mockClient.analyzeCalled, true);
      container.dispose();
    });

    test('submit transitions to noVerifiedData on NO_VERIFIED_DATA response', () async {
      final mockClient = MockApiClient(
        mockResponse: const AnalyzeResponse(
          status: 'NO_VERIFIED_DATA',
          reason: 'no_recognized_symptoms',
        ),
      );
      final container = createContainer(mockClient);
      final notifier = container.read(queryProvider.notifier);

      await notifier.submit('my elbow is itchy');

      final finalState = container.read(queryProvider);
      expect(finalState.phase, QueryPhase.noVerifiedData);
      expect(finalState.noDataReason, 'no_recognized_symptoms');
      container.dispose();
    });

    test('submit transitions to error on ApiException', () async {
      final mockClient = MockApiClient(
        mockError: const ApiException(
          statusCode: 400,
          message: 'Text field must not be empty or whitespace-only.',
        ),
      );
      final container = createContainer(mockClient);
      final notifier = container.read(queryProvider.notifier);

      await notifier.submit('test');

      final finalState = container.read(queryProvider);
      expect(finalState.phase, QueryPhase.error);
      expect(finalState.errorMessage, contains('Text field must not be empty'));
      container.dispose();
    });

    test('reset returns to idle', () async {
      final mockClient = MockApiClient(
        mockResponse: const AnalyzeResponse(
          status: 'NO_VERIFIED_DATA',
          reason: 'no_matching_disease_nodes',
        ),
      );
      final container = createContainer(mockClient);
      final notifier = container.read(queryProvider.notifier);

      await notifier.submit('test');
      expect(container.read(queryProvider).phase, QueryPhase.noVerifiedData);

      notifier.reset();
      expect(container.read(queryProvider).phase, QueryPhase.idle);
      container.dispose();
    });
  });

  group('AnalyzeResponse.fromJson', () {
    test('parses OK response with candidates', () {
      final json = {
        'status': 'OK',
        'reason': '',
        'extracted_symptoms': ['headache'],
        'candidates': [
          {
            'disease_id': 'migraine',
            'name_plain': 'Migraine',
            'confidence_pct': 5,
            'pathognomonic_matches': <String>[],
            'supporting_matches': ['headache'],
            'variants': [
              {'name': 'Migraine with aura', 'notes': 'Visual aura precedes headache.'}
            ],
            'treatments': ['Triptans'],
            'source': 'ICHD-3',
            'clinical_review_status': 'unreviewed',
          }
        ],
      };

      final response = AnalyzeResponse.fromJson(json);
      expect(response.isOk, true);
      expect(response.candidates.length, 1);
      expect(response.candidates[0].diseaseId, 'migraine');
      expect(response.candidates[0].confidencePct, 5);
      expect(response.candidates[0].clinicalReviewStatus, 'unreviewed');
      expect(response.candidates[0].variants.length, 1);
      expect(response.candidates[0].variants[0].name, 'Migraine with aura');
      expect(response.candidates[0].treatments, ['Triptans']);
    });

    test('parses NO_VERIFIED_DATA response', () {
      final json = {
        'status': 'NO_VERIFIED_DATA',
        'reason': 'no_recognized_symptoms',
        'extracted_symptoms': <String>[],
        'candidates': <Map<String, dynamic>>[],
      };

      final response = AnalyzeResponse.fromJson(json);
      expect(response.isNoVerifiedData, true);
      expect(response.reason, 'no_recognized_symptoms');
      expect(response.candidates, isEmpty);
    });
  });
}
